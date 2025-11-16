"""Parser that converts expression text into strategy nodes."""

from __future__ import annotations

import ast
from typing import Any

from ... import indicators as _indicators  # noqa: F401
from ...api.namespace import ensure_namespace_registered
from ...registry.registry import get_global_registry
from .nodes import (
    AggregateNode,
    AttributeNode,
    BinaryNode,
    FilterNode,
    IndicatorNode,
    LiteralNode,
    StrategyError,
    StrategyExpression,
    TimeShiftNode,
    UnaryNode,
)

_BIN_OP_MAP = {
    ast.Add: "add",
    ast.Sub: "sub",
    ast.Mult: "mul",
    ast.Div: "div",
    ast.Mod: "mod",
    ast.Pow: "pow",
}

_COMPARE_MAP = {
    ast.Gt: "gt",
    ast.GtE: "gte",
    ast.Lt: "lt",
    ast.LtE: "lte",
    ast.Eq: "eq",
    ast.NotEq: "neq",
}

_UNARY_MAP = {
    ast.Not: "not",
    ast.UAdd: "pos",
    ast.USub: "neg",
}


class ExpressionParser:
    """Parse Python-esque boolean expressions into strategy nodes."""

    def __init__(self) -> None:
        ensure_namespace_registered()
        # Ensure indicators are loaded before accessing registry
        from ... import indicators  # noqa: F401

        self._registry = get_global_registry()

    def parse_text(self, expression_text: str) -> StrategyExpression:
        expression_text = expression_text.strip()
        if not expression_text:
            raise StrategyError("Expression text cannot be empty")
        try:
            node = ast.parse(expression_text, mode="eval")
        except SyntaxError as exc:  # pragma: no cover - python parser detail
            raise StrategyError(f"Invalid expression: {exc.msg}") from exc
        return self._convert_node(node.body)

    # Node conversions -------------------------------------------------
    def _convert_node(self, node: ast.AST) -> StrategyExpression:
        if isinstance(node, ast.BoolOp):
            return self._convert_bool_op(node)
        if isinstance(node, ast.BinOp):
            return self._convert_bin_op(node)
        if isinstance(node, ast.Compare):
            return self._convert_compare(node)
        if isinstance(node, ast.UnaryOp):
            return self._convert_unary_op(node)
        if isinstance(node, ast.Call):
            return self._convert_indicator_call(node)
        if isinstance(node, ast.Constant):
            return self._convert_constant(node)
        if isinstance(node, ast.Name):
            return self._convert_name(node)
        if isinstance(node, ast.Attribute):
            return self._convert_attribute(node)
        raise StrategyError(f"Unsupported expression element '{ast.dump(node)}'")

    def _convert_bool_op(self, node: ast.BoolOp) -> StrategyExpression:
        operator = "and" if isinstance(node.op, ast.And) else "or"
        if len(node.values) < 2:
            raise StrategyError("Boolean operations require at least two operands")
        expr = self._convert_node(node.values[0])
        for value in node.values[1:]:
            expr = BinaryNode(operator=operator, left=expr, right=self._convert_node(value))
        return expr

    def _convert_bin_op(self, node: ast.BinOp) -> StrategyExpression:
        operator = _BIN_OP_MAP.get(type(node.op))
        if not operator:
            raise StrategyError(f"Unsupported operator '{ast.dump(node.op)}'")
        return BinaryNode(
            operator=operator,
            left=self._convert_node(node.left),
            right=self._convert_node(node.right),
        )

    def _convert_compare(self, node: ast.Compare) -> StrategyExpression:
        if len(node.ops) != len(node.comparators):
            raise StrategyError("Malformed comparison expression")
        left = self._convert_node(node.left)
        result: StrategyExpression | None = None
        for op, comparator in zip(node.ops, node.comparators, strict=False):
            operator = _COMPARE_MAP.get(type(op))
            if not operator:
                raise StrategyError(f"Unsupported comparison operator '{ast.dump(op)}'")
            right = self._convert_node(comparator)
            comparison = BinaryNode(operator=operator, left=left, right=right)
            result = comparison if result is None else BinaryNode(operator="and", left=result, right=comparison)
            left = right
        assert result is not None
        return result

    def _convert_unary_op(self, node: ast.UnaryOp) -> StrategyExpression:
        operator = _UNARY_MAP.get(type(node.op))
        if not operator:
            raise StrategyError(f"Unsupported unary operator '{ast.dump(node.op)}'")
        return UnaryNode(operator=operator, operand=self._convert_node(node.operand))

    def _convert_indicator_call(self, node: ast.Call) -> StrategyExpression:
        # Check if this is a method call on an attribute (e.g., trades.filter(...), trades.sum(...))
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr.lower()

            # Handle filter() calls: trades.filter(amount > 1000000)
            if method_name == "filter":
                if len(node.args) != 1:
                    raise StrategyError("filter() requires exactly one argument (the condition)")
                series_expr = self._convert_node(node.func.value)
                condition_expr = self._convert_node(node.args[0])
                return FilterNode(series=series_expr, condition=condition_expr)

            # Handle aggregation method calls: trades.sum(amount), trades.avg(price)
            if method_name in {"sum", "avg", "max", "min"}:
                series_expr = self._convert_node(node.func.value)
                field: str | None = None

                if len(node.args) == 1:
                    # Extract field name from argument
                    arg = node.args[0]
                    if isinstance(arg, ast.Name):
                        field = arg.id
                    elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        field = arg.value
                    else:
                        raise StrategyError(f"{method_name}() requires a field name as argument")
                elif len(node.args) > 1:
                    raise StrategyError(f"{method_name}() accepts at most one argument (field name)")

                return AggregateNode(series=series_expr, operation=method_name, field=field)

            # If it's not a recognized method, fall through to error

        # Handle regular indicator calls
        if not isinstance(node.func, ast.Name):
            raise StrategyError("Only simple indicator function calls are allowed")
        name = node.func.id.lower()

        if name == "select":
            return self._convert_select_call(node)

        # Ensure indicators are loaded (in case registry was cleared)
        from ... import indicators  # noqa: F401

        descriptor = self._registry.get(name)
        if descriptor is None:
            raise StrategyError(f"Indicator '{name}' not found")

        param_defs = [
            param for param in descriptor.schema.parameters.values() if param.name.lower() not in {"ctx", "context"}
        ]
        params: dict[str, Any] = {}
        input_expr: StrategyExpression | None = None

        supports_nested = name in {
            "crossup",
            "crossdown",
            "cross",
            "rising",
            "falling",
            "rising_pct",
            "falling_pct",
            "in",
            "in_channel",
            "out",
            "enter",
            "exit",
        }

        # Check if first positional argument is an expression (for explicit source input)
        # This affects how we count arguments
        # This allows patterns like sma(BTC.price, period=20) or sma(trades.volume, period=20)
        if len(node.args) > 0:
            first_arg = node.args[0]
            # Try to convert as expression first - if it fails, fall back to literal
            # Check if this looks like an expression (attribute access, binary op, etc.)
            # Note: ast.Constant is NOT included - constants should be treated as literals first
            is_expression_type = isinstance(
                first_arg,
                (ast.Attribute | ast.Call | ast.BinOp | ast.UnaryOp | ast.Compare | ast.BoolOp),
            )

            if is_expression_type:
                # This is an expression - try to convert it
                try:
                    input_expr = self._convert_node(first_arg)
                    # Successfully converted as expression - skip adding it to params
                except StrategyError:
                    # Expression conversion failed - try as literal as fallback
                    try:
                        literal_val = self._literal_value(first_arg)
                        if len(param_defs) > 0:
                            param_name = param_defs[0].name
                            params[param_name] = literal_val
                    except StrategyError:
                        raise StrategyError(
                            f"Indicator '{name}' first argument must be a literal value or valid expression"
                        ) from None
            else:
                # Not an expression type - try as literal first
                try:
                    literal_val = self._literal_value(first_arg)
                    if len(param_defs) > 0:
                        param_name = param_defs[0].name
                        params[param_name] = literal_val
                except StrategyError:
                    # Literal failed - try as expression as fallback
                    try:
                        input_expr = self._convert_node(first_arg)
                    except StrategyError:
                        raise StrategyError(
                            f"Indicator '{name}' first argument must be a literal value or valid expression"
                        ) from None

            # Process remaining positional arguments (starting from index 1)
            # If input_expr was set: args[0] is expression (stored separately), args[1..] map to param_defs[0..]
            # If input_expr was not set: args[0] was assigned to param_defs[0], args[1..] map to param_defs[1..]
            for arg_index in range(1, len(node.args)):
                # Map arg_index to param_index
                # If input_expr: args[1] -> param_defs[0], args[2] -> param_defs[1], etc.
                # If no input_expr: args[1] -> param_defs[1], args[2] -> param_defs[2], etc.
                param_index = (arg_index - 1) if input_expr is not None else arg_index
                if param_index >= len(param_defs):
                    break
                param_name = param_defs[param_index].name
                params[param_name] = self._literal_or_expression(
                    node.args[arg_index], supports_nested, name, param_name
                )

            # Validate argument count
            # If input_expr is present, we allow one extra positional arg (the expression)
            max_allowed = len(param_defs) + (1 if input_expr is not None else 0)
            if len(node.args) > max_allowed:
                raise StrategyError(
                    f"Indicator '{name}' accepts at most {len(param_defs)} positional arguments"
                    + (" (plus one expression as input)" if input_expr is not None else "")
                )
        else:
            # No positional args - process keyword args normally
            pass

        for keyword in node.keywords:
            if keyword.arg is None:
                raise StrategyError("Keyword arguments must specify parameter names")
            if keyword.arg.lower() in {"ctx", "context"}:
                raise StrategyError("Context argument is managed automatically and cannot be overridden")
            # Check if this parameter was already set from a positional argument
            if keyword.arg in params:
                raise StrategyError(
                    f"Indicator '{name}' parameter '{keyword.arg}' cannot be specified both as positional and keyword argument"
                )
            params[keyword.arg] = self._literal_or_expression(keyword.value, supports_nested, name, keyword.arg)

        return IndicatorNode(name=name, params=params, input_expr=input_expr)

    def _convert_select_call(self, node: ast.Call) -> IndicatorNode:
        params: dict[str, Any] = {}
        if len(node.args) > 1:
            raise StrategyError("select() expects at most one positional argument")
        if len(node.args) == 1:
            field_value = self._literal_value(node.args[0])
            if not isinstance(field_value, str):
                raise StrategyError("select() field parameter must be a string literal")
            params["field"] = field_value.lower()
        for keyword in node.keywords:
            if keyword.arg is None:
                raise StrategyError("Keyword arguments must specify parameter names")
            params[keyword.arg] = self._literal_value(keyword.value)
        return IndicatorNode(name="select", params=params)

    def _convert_constant(self, node: ast.Constant) -> LiteralNode:
        value = node.value
        if isinstance(value, bool):
            return LiteralNode(value=1.0 if value else 0.0)
        if isinstance(value, int | float):
            return LiteralNode(value=float(value))
        raise StrategyError(f"Unsupported literal value '{value}'")

    def _convert_name(self, node: ast.Name) -> StrategyExpression:
        lowered = node.id.lower()
        if lowered in {"true", "false"}:
            return LiteralNode(value=1.0 if lowered == "true" else 0.0)
        valid_fields = {
            "close",
            "high",
            "low",
            "open",
            "volume",
            "hlc3",
            "ohlc4",
            "hl2",
            "typical_price",
            "weighted_close",
            "median_price",
            "range",
            "upper_wick",
            "lower_wick",
        }
        if lowered in valid_fields:
            return IndicatorNode(name="select", params={"field": lowered})
        raise StrategyError(f"Unknown identifier '{node.id}'")

    def _convert_attribute(self, node: ast.Attribute) -> StrategyExpression:
        """Convert attribute access like BTC.trades.volume or binance.BTC.orderbook.imbalance"""
        # Check if this might be an aggregation property (e.g., trades.count)
        # Aggregation properties: count
        aggregation_properties = {"count"}

        # Check if this is a time-shift suffix (e.g., price.24h_ago, volume.change_pct_24h)
        last_attr = node.attr.lower()
        time_shift_pattern = self._parse_time_shift_suffix(last_attr)

        if time_shift_pattern:
            # This is a time-shift operation
            shift, operation = time_shift_pattern
            series_expr = self._convert_node(node.value)
            return TimeShiftNode(series=series_expr, shift=shift, operation=operation)

        # If the last attribute is an aggregation property, treat it as an aggregation
        if last_attr in aggregation_properties:
            # Get the series expression (everything before the aggregation property)
            series_expr = self._convert_node(node.value)
            return AggregateNode(series=series_expr, operation=last_attr, field=None)

        # Otherwise, treat as regular attribute access
        # Build chain: [binance, BTC, 1h, trades, volume] or [BTC, trades, volume]
        # Only support attribute chain format (no bracket notation)
        chain = []
        current = node
        while isinstance(current, ast.Attribute):
            chain.insert(0, current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            chain.insert(0, current.id)
        else:
            raise StrategyError(f"Unsupported attribute chain base: {ast.dump(current)}")

        # Parse chain into components (now includes base, quote, instrument_type)
        exchange, symbol, timeframe, source, field, base, quote, instrument_type = self._parse_attribute_chain(chain)

        # Validate the combination
        self._validate_attribute_combination(exchange, symbol, timeframe, source, field)

        return AttributeNode(
            symbol=symbol,
            field=field,
            exchange=exchange,
            timeframe=timeframe,
            source=source,
            base=base,
            quote=quote,
            instrument_type=instrument_type,
        )

    def _parse_attribute_chain(
        self, chain: list[str]
    ) -> tuple[str | None, str, str | None, str, str, str | None, str | None, str | None]:
        """
        Parse attribute chain into (exchange, symbol, timeframe, source, field, base, quote, instrument_type).

        Examples:
        - [BTC, trades, volume] -> (None, BTC, None, trades, volume, None, None, None)
        - [binance, BTC, price] -> (binance, BTC, None, ohlcv, price, None, None, None)
        - [BTC, USDT, perp, price] -> (None, BTC/USDT, None, ohlcv, price, BTC, USDT, perp)
        - [BTC, USDT, spot, price] -> (None, BTC/USDT, None, ohlcv, price, BTC, USDT, spot)
        - [binance, BTC, USDT, perp, 1h, price] -> (binance, BTC/USDT, 1h, ohlcv, price, BTC, USDT, perp)
        - [BTC, USDT, perp, trades, volume] -> (None, BTC/USDT, None, trades, volume, BTC, USDT, perp)
        """
        if len(chain) < 2:
            raise StrategyError(f"Attribute chain too short: {'.'.join(chain)}")

        # Known exchanges (can be extended)
        known_exchanges = {"binance", "bybit", "okx", "coinbase", "kraken", "kucoin"}
        # Known sources
        known_sources = {"ohlcv", "trades", "orderbook", "liquidation"}
        # Known timeframes (common patterns)
        # Note: Python AST can't parse numeric identifiers like "1h", so we support alternative formats:
        # - "h1" for "1h", "m15" for "15m", "d1" for "1d", etc.
        # - Also support original format "1h", "15m" if they appear in bracket notation (not supported now)
        timeframe_patterns = {
            # Alternative format (Python-valid identifiers)
            "m1",
            "m3",
            "m5",
            "m15",
            "m30",
            "h1",
            "h2",
            "h4",
            "h6",
            "h8",
            "h12",
            "d1",
            "d3",
            "w1",
            "mo1",
            # Original format (for reference, but can't be used in attribute chains)
            "1m",
            "5m",
            "15m",
            "30m",
            "1h",
            "4h",
            "1d",
            "1w",
            "1mo",
        }
        # Known instrument types
        instrument_types = {"spot", "perp", "perpetual", "futures", "future", "option"}

        exchange: str | None = None
        symbol: str | None = None
        timeframe: str | None = None
        source: str = "ohlcv"
        field: str | None = None
        base: str | None = None
        quote: str | None = None
        instrument_type: str | None = None

        # Check if first element is an exchange
        if chain[0].lower() in known_exchanges:
            exchange = chain[0].lower()
            chain = chain[1:]
            if len(chain) < 1:
                raise StrategyError("Missing symbol after exchange")

        if len(chain) < 1:
            raise StrategyError("Missing symbol in attribute chain")

        # Known field names (check these before treating as quote)
        known_fields = {
            "close",
            "high",
            "low",
            "open",
            "volume",
            "hlc3",
            "ohlc4",
            "typical_price",
            "weighted_close",
            "median_price",
            "range",
            "upper_wick",
            "lower_wick",
            "price",
            "amount",
            "count",
            "bid",
            "ask",
            "bid_size",
            "ask_size",
            "imbalance",
            "liquidation",
        }

        # Check if we have Base/Quote pattern in chain: [BASE, QUOTE, instrument_type?, ...]
        # Look ahead to see if next element could be a quote
        if len(chain) >= 2:
            potential_base = chain[0]
            potential_quote = chain[1]
            # Check if potential_quote looks like a quote asset (3-4 chars, case-insensitive)
            # and is not a known source, timeframe, instrument type, or field name
            potential_quote_lower = potential_quote.lower()
            if (
                len(potential_quote) >= 3
                and len(potential_quote) <= 4
                and potential_quote_lower not in known_sources
                and potential_quote_lower not in timeframe_patterns
                and potential_quote_lower not in instrument_types
                and potential_quote_lower not in known_fields
                and potential_quote.isalnum()  # Quote assets are alphanumeric (USDT, USDC, USD, etc.)
            ):
                # This looks like Base/Quote format (case-insensitive)
                base = potential_base.upper()
                quote = potential_quote.upper()
                symbol = f"{base}/{quote}"
                chain = chain[2:]  # Consume BASE and QUOTE

                # Check if next element is an instrument type
                if len(chain) > 0 and chain[0].lower() in instrument_types:
                    instrument_type = chain[0].lower()
                    # Normalize instrument type
                    if instrument_type in {"perp", "perpetual"}:
                        instrument_type = "perp"
                    elif instrument_type in {"futures", "future"}:
                        instrument_type = "futures"
                    chain = chain[1:]  # Consume instrument type
            else:
                # Not Base/Quote format, use simple symbol
                symbol = chain[0]
                chain = chain[1:]
        else:
            # Not enough elements for Base/Quote, use simple symbol
            symbol = chain[0]
            chain = chain[1:]

        if len(chain) == 0:
            raise StrategyError(f"Missing field in attribute chain: {symbol}")

        # Try to identify timeframe, source, and field
        # We need at least one element (the field), and optionally timeframe and source
        # Timeframes use alternative format: h1 (1h), m15 (15m), d1 (1d), etc.

        # Helper function to normalize timeframe format
        def normalize_timeframe(tf: str) -> str:
            """Convert alternative format (h1, m15) to standard format (1h, 15m)."""
            if len(tf) >= 2 and tf[0].isalpha() and tf[1:].isdigit():
                # Format: h1, m15, d1, etc. -> convert to 1h, 15m, 1d
                unit = tf[0]
                value = tf[1:]
                return f"{value}{unit}"
            return tf  # Return as-is if already in standard format

        # If we have 2+ elements, check if second-to-last is a source
        # If we have 3+ elements, check if second is timeframe and third is source
        if len(chain) == 1:
            # Single element: could be a field (default ohlcv) or a source (if it's a known source)
            # Check if it's a known source - if so, treat as source with no field (for aggregation)
            if chain[0].lower() in known_sources:
                source = chain[0].lower()
                field = None  # No field yet - will be set by aggregation
            else:
                # Simple case: [field] -> default to ohlcv
                field = chain[0]
        elif len(chain) == 2:
            # Two possibilities:
            # 1. [timeframe, field] -> default to ohlcv
            # 2. [source, field]
            # 3. [instrument_type, field] -> if instrument_type wasn't consumed yet
            if chain[0] in timeframe_patterns:
                timeframe = normalize_timeframe(chain[0])
                field = chain[1]
            elif chain[0].lower() in known_sources:
                source = chain[0].lower()
                field = chain[1]
            elif chain[0].lower() in instrument_types:
                # Instrument type after base/quote (if not already consumed)
                inst_type = chain[0].lower()
                if inst_type in {"perp", "perpetual"}:
                    instrument_type = "perp"
                elif inst_type in {"futures", "future"}:
                    instrument_type = "futures"
                else:
                    instrument_type = inst_type
                field = chain[1]
            else:
                # Assume it's [source, field] even if source not recognized
                # This allows for flexibility
                source = chain[0].lower()
                field = chain[1]
        elif len(chain) == 3:
            # Three elements: multiple possibilities
            # 1. [timeframe, source, field]
            # 2. [timeframe, instrument_type, field]
            # 3. [instrument_type, timeframe, field] (less common)
            if chain[0] in timeframe_patterns:
                timeframe = normalize_timeframe(chain[0])
                # Check if second element is source or instrument_type
                if chain[1].lower() in known_sources:
                    source = chain[1].lower()
                    field = chain[2]
                elif chain[1].lower() in instrument_types:
                    # [timeframe, instrument_type, field]
                    inst_type = chain[1].lower()
                    if inst_type in {"perp", "perpetual"}:
                        instrument_type = "perp"
                    elif inst_type in {"futures", "future"}:
                        instrument_type = "futures"
                    else:
                        instrument_type = inst_type
                    field = chain[2]
                else:
                    raise StrategyError(
                        f"Invalid attribute chain format. After timeframe '{chain[0]}', expected source or instrument_type, "
                        f"got '{chain[1]}'. Chain: {'.'.join(chain)}"
                    )
            elif chain[0].lower() in instrument_types:
                # [instrument_type, timeframe, field] or [instrument_type, source, field]
                inst_type = chain[0].lower()
                if inst_type in {"perp", "perpetual"}:
                    instrument_type = "perp"
                elif inst_type in {"futures", "future"}:
                    instrument_type = "futures"
                else:
                    instrument_type = inst_type
                if chain[1] in timeframe_patterns:
                    timeframe = normalize_timeframe(chain[1])
                    field = chain[2]
                elif chain[1].lower() in known_sources:
                    source = chain[1].lower()
                    field = chain[2]
                else:
                    raise StrategyError(
                        f"Invalid attribute chain format. After instrument_type '{chain[0]}', expected timeframe or source, "
                        f"got '{chain[1]}'. Chain: {'.'.join(chain)}"
                    )
            elif chain[0].lower() in known_sources:
                # [source, timeframe, field] or [source, instrument_type, field]
                source = chain[0].lower()
                if chain[1] in timeframe_patterns:
                    timeframe = normalize_timeframe(chain[1])
                    field = chain[2]
                elif chain[1].lower() in instrument_types:
                    inst_type = chain[1].lower()
                    if inst_type in {"perp", "perpetual"}:
                        instrument_type = "perp"
                    elif inst_type in {"futures", "future"}:
                        instrument_type = "futures"
                    else:
                        instrument_type = inst_type
                    field = chain[2]
                else:
                    raise StrategyError(
                        f"Invalid attribute chain format. After source '{chain[0]}', expected timeframe or instrument_type, "
                        f"got '{chain[1]}'. Chain: {'.'.join(chain)}"
                    )
            else:
                raise StrategyError(
                    f"Invalid attribute chain format. Expected: symbol.timeframe.source.field, "
                    f"symbol.timeframe.instrument_type.field, symbol.source.field, or symbol.instrument_type.field, "
                    f"got: {'.'.join(chain)}"
                )
        elif len(chain) == 4:
            # Four elements: [timeframe, instrument_type, source, field] or [instrument_type, timeframe, source, field]
            if chain[0] in timeframe_patterns:
                timeframe = normalize_timeframe(chain[0])
                if chain[1].lower() in instrument_types:
                    inst_type = chain[1].lower()
                    if inst_type in {"perp", "perpetual"}:
                        instrument_type = "perp"
                    elif inst_type in {"futures", "future"}:
                        instrument_type = "futures"
                    else:
                        instrument_type = inst_type
                    if chain[2].lower() in known_sources:
                        source = chain[2].lower()
                        field = chain[3]
                    else:
                        raise StrategyError(
                            f"Invalid attribute chain format. Expected source after timeframe and instrument_type, "
                            f"got '{chain[2]}'. Chain: {'.'.join(chain)}"
                        )
                else:
                    raise StrategyError(
                        f"Invalid attribute chain format. Expected instrument_type after timeframe, "
                        f"got '{chain[1]}'. Chain: {'.'.join(chain)}"
                    )
            elif chain[0].lower() in instrument_types:
                inst_type = chain[0].lower()
                if inst_type in {"perp", "perpetual"}:
                    instrument_type = "perp"
                elif inst_type in {"futures", "future"}:
                    instrument_type = "futures"
                else:
                    instrument_type = inst_type
                if chain[1] in timeframe_patterns:
                    timeframe = normalize_timeframe(chain[1])
                    if chain[2].lower() in known_sources:
                        source = chain[2].lower()
                        field = chain[3]
                    else:
                        raise StrategyError(
                            f"Invalid attribute chain format. Expected source after instrument_type and timeframe, "
                            f"got '{chain[2]}'. Chain: {'.'.join(chain)}"
                        )
                else:
                    raise StrategyError(
                        f"Invalid attribute chain format. Expected timeframe after instrument_type, "
                        f"got '{chain[1]}'. Chain: {'.'.join(chain)}"
                    )
            else:
                raise StrategyError(
                    f"Invalid attribute chain format. Expected timeframe or instrument_type at start, "
                    f"got '{chain[0]}'. Chain: {'.'.join(chain)}"
                )
        else:
            raise StrategyError(f"Attribute chain too long: {'.'.join(chain)}")

        return exchange, symbol, timeframe, source, field, base, quote, instrument_type

    def _validate_attribute_combination(
        self,
        exchange: str | None,
        symbol: str,
        timeframe: str | None,
        source: str,
        field: str,
    ) -> None:
        """Validate that the attribute combination is valid."""
        # Known sources and their allowed fields
        source_fields = {
            "ohlcv": {
                "price",
                "close",
                "open",
                "high",
                "low",
                "volume",
                "hlc3",
                "ohlc4",
                "hl2",
                "typical_price",
                "weighted_close",
                "median_price",
                "range",
                "upper_wick",
                "lower_wick",
            },
            "trades": {
                "volume",
                "count",
                "buy_volume",
                "sell_volume",
                "large_count",
                "whale_count",
                "avg_price",
                "vwap",
                "amount",
            },
            "orderbook": {
                "best_bid",
                "best_ask",
                "spread",
                "spread_bps",
                "mid_price",
                "bid_depth",
                "ask_depth",
                "imbalance",
                "pressure",
            },
            "liquidation": {
                "count",
                "volume",
                "value",
                "long_count",
                "short_count",
                "long_value",
                "short_value",
                "large_count",
                "large_value",
            },
        }

        # Validate source
        if source not in source_fields:
            raise StrategyError(f"Unknown source '{source}'. Valid sources: {', '.join(source_fields.keys())}")

        # Validate field for source (if field is provided)
        if field is not None:
            if field.lower() not in source_fields[source]:
                valid_fields = ", ".join(sorted(source_fields[source]))
                raise StrategyError(
                    f"Field '{field}' not valid for source '{source}'. Valid fields for {source}: {valid_fields}"
                )
        # If field is None, it's likely being used in an aggregation context (e.g., liquidation.count)
        # This is valid - the aggregation will handle the field selection

    def _parse_time_shift_suffix(self, attr: str) -> tuple[str, str | None] | None:
        """
        Parse time-shift suffix from attribute name.

        Returns (shift, operation) if it's a time-shift suffix, None otherwise.

        Examples:
        - "24h_ago" -> ("24h_ago", None)
        - "1h_ago" -> ("1h_ago", None)
        - "change_pct_24h" -> ("24h", "change_pct")
        - "change_24h" -> ("24h", "change")
        - "roc_24" -> ("24", "roc")  # Rate of change with period
        """
        import re

        # Pattern for time periods: number followed by unit (h, m, d, w, mo)
        time_pattern = r"(\d+)([hmdw]|mo)"

        # Check for simple time-shift suffixes: Xh_ago, Xm_ago, Xd_ago, etc.
        if attr.endswith("_ago"):
            time_part = attr[:-4]  # Remove "_ago"
            if re.match(rf"^{time_pattern}$", time_part):
                return (attr, None)

        # Check for operation-based time shifts: change_pct_24h, change_1h, roc_24
        # Pattern: operation_timeperiod
        operation_patterns = {
            "change_pct": r"change_pct_(\d+[hmdw]|mo)",
            "change": r"change_(\d+[hmdw]|mo)",
            "roc": r"roc_(\d+)",  # Rate of change with period (no unit, just number)
        }

        for operation, pattern in operation_patterns.items():
            match = re.match(rf"^{pattern}$", attr)
            if match:
                shift = match.group(1)
                return (shift, operation)

        # Check for simple time period without operation: 24h, 1h, etc.
        if re.match(rf"^{time_pattern}$", attr):
            return (attr, None)

        return None

    # Helpers -----------------------------------------------------------
    def _literal_value(self, node: ast.AST) -> Any:
        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, int | float | str | bool):
                return value
            raise StrategyError(f"Unsupported literal type '{type(value).__name__}'")

        if (
            isinstance(node, ast.UnaryOp)
            and isinstance(node.op, ast.USub | ast.UAdd)
            and isinstance(node.operand, ast.Constant)
        ):
            value = node.operand.value
            if not isinstance(value, int | float):
                raise StrategyError("Only numeric literals can be negated")
            return -value if isinstance(node.op, ast.USub) else value

        raise StrategyError("Only literal values are allowed inside indicator parameters")

    def _literal_or_expression(self, node: ast.AST, allow_expression: bool, indicator: str, param: str) -> Any:
        try:
            return self._literal_value(node)
        except StrategyError:
            if allow_expression:
                return self._convert_node(node)
            raise StrategyError(
                f"Indicator '{indicator}' parameter '{param}' must be a literal value; nested expressions are not supported"
            ) from None
