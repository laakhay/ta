"""High-performance Series data structure for time series data."""

from __future__ import annotations

import decimal
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any, Generic, Literal, TypeAlias, TypeVar

from .types import Price, Qty, Symbol, Timestamp

T = TypeVar("T")


@dataclass(slots=True, frozen=True)
class Series(Generic[T]):
    """Immutable time series with generic value type."""

    timestamps: tuple[Timestamp, ...]  # Sorted timestamps
    values: tuple[T, ...]  # Corresponding values
    symbol: Symbol  # Trading symbol
    timeframe: str  # Timeframe (e.g., '1h', '4h')
    availability_mask: tuple[bool, ...] | None = None  # True where value is valid/available

    def __post_init__(self) -> None:
        """Validate series data integrity after initialization."""
        if len(self.timestamps) != len(self.values):
            raise ValueError("Timestamps and values must have the same length")

        if len(self.timestamps) > 1:
            if any(later < earlier for earlier, later in zip(self.timestamps, self.timestamps[1:], strict=False)):
                raise ValueError("Timestamps must be sorted")

        if self.availability_mask is not None and len(self.availability_mask) != len(self.timestamps):
            raise ValueError("Availability mask must match length of series")

    @property
    def length(self) -> int:
        """Number of data points in the series."""
        return len(self.timestamps)

    @property
    def is_empty(self) -> bool:
        """Whether the series is empty."""
        return self.length == 0

    def __len__(self) -> int:
        return self.length

    def __getitem__(self, index: int | slice) -> tuple[Timestamp, T] | Series[T]:
        """Access single data point or slice the series."""
        try:
            if isinstance(index, int):
                return self.timestamps[index], self.values[index]
            else:
                # Handle slice case
                return Series[T](
                    timestamps=self.timestamps[index],
                    values=self.values[index],
                    symbol=self.symbol,
                    timeframe=self.timeframe,
                )
        except (TypeError, KeyError) as e:
            if "indices must be integers or slices" in str(e):
                raise TypeError("Series indices must be integers or slices") from e
            raise

    def __iter__(self) -> Iterator[tuple[Timestamp, T]]:
        """Iterate over (timestamp, value) pairs."""
        return zip(self.timestamps, self.values, strict=False)

    def __add__(self, other: Series[T] | T) -> Series[T]:
        """Element-wise addition or scalar addition."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="add")
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values, strict=False):
                    new_values_list.append(v1 + v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(f"Cannot add series values of types {type(self.values[0])} and {type(other.values[0])}")

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )
        else:
            # Scalar addition (requires T to support addition)
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v + other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot add {type(other)} to series values of type {type(self.values[0]) if self.values else 'unknown'}"
                )
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

    def __sub__(self, other: Series[T] | T) -> Series[T]:
        """Subtract scalar or element-wise subtract series."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="subtract")
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values, strict=False):
                    new_values_list.append(v1 - v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot subtract series values of types {type(self.values[0])} and {type(other.values[0])}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=_and_masks(self.availability_mask, other.availability_mask),
            )
        else:
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v - other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot subtract {type(other)} from series values of type {type(self.values[0]) if self.values else 'unknown'}"
                )
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

    def __mul__(self, other: Series[T] | T) -> Series[T]:
        """Multiply series by scalar or element-wise multiply by series."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="multiply")
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values, strict=False):
                    new_values_list.append(v1 * v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot multiply series values of types {type(self.values[0])} and {type(other.values[0])}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=_and_masks(self.availability_mask, other.availability_mask),
            )
        else:
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v * other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot multiply series values of type {type(self.values[0]) if self.values else 'unknown'} by {type(other)}"
                )
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

    def __truediv__(self, other: Series[T] | T) -> Series[T]:
        """Divide series by scalar or element-wise divide by series."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="divide")
            try:
                new_values_list = []
                for v1, v2 in zip(self.values, other.values, strict=False):
                    new_values_list.append(v1 / v2)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot divide series values of types {type(self.values[0])} and {type(other.values[0])}"
                )
            except ZeroDivisionError:
                raise ValueError("Cannot divide by zero in series")

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=_and_masks(self.availability_mask, other.availability_mask),
            )
        else:
            try:
                new_values_list = []
                for v in self.values:
                    new_values_list.append(v / other)  # type: ignore
                new_values = tuple(new_values_list)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot divide series values of type {type(self.values[0]) if self.values else 'unknown'} by {type(other)}"
                )
            except ZeroDivisionError:
                raise ValueError("Cannot divide by zero")
            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

    def __mod__(self, other: Series[T] | T) -> Series[T]:
        """Modulo operation between series or with scalar."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="modulo")
            try:
                new_values = tuple(v1 % v2 for v1, v2 in zip(self.values, other.values, strict=False))  # type: ignore[misc]
            except (ZeroDivisionError, decimal.InvalidOperation):
                raise ValueError("Cannot perform modulo with zero divisor in series") from None
            except TypeError:
                raise TypeError(
                    f"Cannot perform modulo on series values of types {type(self.values[0])} and {type(other.values[0])}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=_and_masks(self.availability_mask, other.availability_mask),
            )
        else:
            try:
                new_values = []
                for v in self.values:
                    new_values.append(v % other)  # type: ignore
            except (ZeroDivisionError, decimal.InvalidOperation):
                raise ValueError("Cannot perform modulo with scalar zero") from None
            except TypeError:
                raise TypeError(
                    f"Cannot perform modulo on series values of type {type(self.values[0]) if self.values else 'unknown'} with scalar {type(other)}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=tuple(new_values),  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

    def __pow__(self, other: Series[T] | T) -> Series[T]:
        """Power operation between series or with scalar exponent."""
        if isinstance(other, Series):
            self._validate_series_alignment(other, operation="power")
            try:
                new_values = tuple(v1**v2 for v1, v2 in zip(self.values, other.values, strict=False))  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot perform power on series values of types {type(self.values[0])} and {type(other.values[0])}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )
        else:
            try:
                new_values = tuple(v**other for v in self.values)  # type: ignore[misc]
            except TypeError:
                raise TypeError(
                    f"Cannot perform power on series values of type {type(self.values[0]) if self.values else 'unknown'} with scalar {type(other)}"
                )

            return Series[T](
                timestamps=self.timestamps,
                values=new_values,  # type: ignore[arg-type]
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

    def __neg__(self) -> Series[T]:
        """Unary negation of series."""
        try:
            new_values_list = []
            for v in self.values:
                new_values_list.append(-v)  # type: ignore
            new_values = tuple(new_values_list)  # type: ignore[misc]
        except TypeError:
            raise TypeError(f"Cannot negate series values of type {type(self.values[0]) if self.values else 'unknown'}")
        return Series[T](
            timestamps=self.timestamps,
            values=new_values,  # type: ignore[arg-type]
            symbol=self.symbol,
            timeframe=self.timeframe,
            availability_mask=self.availability_mask,
        )

    def __pos__(self) -> Series[T]:
        """Unary plus of series (returns copy)."""
        return Series[T](
            timestamps=self.timestamps,
            values=self.values,
            symbol=self.symbol,
            timeframe=self.timeframe,
            availability_mask=self.availability_mask,
        )

    def slice_by_time(self, start: Timestamp, end: Timestamp) -> Series[T]:
        """Slice series by time range using binary search for efficiency."""
        if start > end:
            raise ValueError("Start time must be <= end time")

        # Binary search for start index
        left, right = 0, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] < start:
                left = mid + 1
            else:
                right = mid
        start_idx = left

        # Binary search for end index
        left, right = start_idx, len(self.timestamps)
        while left < right:
            mid = (left + right) // 2
            if self.timestamps[mid] <= end:
                left = mid + 1
            else:
                right = mid
        end_idx = left

        return Series[T](
            timestamps=self.timestamps[start_idx:end_idx],
            values=self.values[start_idx:end_idx],
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def filter(self, condition: Series[bool]) -> Series[T]:
        """Filter series based on boolean condition.

        Args:
            condition: Boolean series indicating which elements to keep (True = keep).

        Returns:
            New series containing only elements where condition is True.

        Raises:
            ValueError: If condition series is not aligned with this series.
        """
        self._validate_series_alignment(condition, operation="filter")
        filtered_timestamps: list[Timestamp] = []
        filtered_values: list[T] = []
        filtered_mask: list[bool] | None = None if self.availability_mask is None else []

        for i, (ts, val, cond_val) in enumerate(zip(self.timestamps, self.values, condition.values, strict=False)):
            if cond_val:  # Keep elements where condition is True
                filtered_timestamps.append(ts)
                filtered_values.append(val)
                if filtered_mask is not None:
                    filtered_mask.append(self.availability_mask[i] if self.availability_mask is not None else True)

        return Series[T](
            timestamps=tuple(filtered_timestamps),
            values=tuple(filtered_values),
            symbol=self.symbol,
            timeframe=self.timeframe,
            availability_mask=tuple(filtered_mask) if filtered_mask is not None else None,
        )

    def count(self) -> Series[int]:
        """Count elements in series.

        Returns:
            Series with a single value representing the count of elements.
            For empty series, returns a series with a single value of 0.
        """
        count_value = len(self.values)
        # Always return a series with a single value, even for empty input
        # Use first timestamp if available, otherwise create a placeholder
        if self.timestamps:
            timestamp = self.timestamps[0]
        else:
            # For empty series, we need a timestamp - use a default
            from datetime import UTC, datetime

            timestamp = datetime.now(UTC)
        return Series[int](
            timestamps=(timestamp,),
            values=(count_value,),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def sum(self, field: str | None = None) -> Series[float]:
        """Sum values in series.

        Args:
            field: Optional field name (for future use with structured data).

        Returns:
            Series with a single value representing the sum.
            For empty series, returns a series with a single value of 0.0.
        """
        from decimal import Decimal

        # For now, sum the values directly
        # In the future, if values are structured objects, field can be used
        if len(self.values) == 0:
            total = 0.0
        else:
            total = sum(
                float(Decimal(str(v))) if not isinstance(v, int | float | Decimal) else float(v) for v in self.values
            )

        # Always return a series with a single value
        # Use first timestamp if available, otherwise create a placeholder
        if self.timestamps:
            timestamp = self.timestamps[0]
        else:
            # For empty series, we need a timestamp - use a default
            from datetime import UTC, datetime

            timestamp = datetime.now(UTC)

        return Series[float](
            timestamps=(timestamp,),
            values=(total,),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def avg(self, field: str | None = None) -> Series[float]:
        """Average values in series.

        Args:
            field: Optional field name (for future use with structured data).

        Returns:
            Series with a single value representing the average.
        """
        from decimal import Decimal

        if len(self.values) == 0:
            return Series[float](
                timestamps=(),
                values=(),
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

        total = sum(
            float(Decimal(str(v))) if not isinstance(v, int | float | Decimal) else float(v) for v in self.values
        )
        avg_value = total / len(self.values)
        return Series[float](
            timestamps=(self.timestamps[0],) if self.timestamps else (),
            values=(avg_value,),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def max(self, field: str | None = None) -> Series[T]:
        """Maximum value in series.

        Args:
            field: Optional field name (for future use with structured data).

        Returns:
            Series with a single value representing the maximum.
        """
        if len(self.values) == 0:
            return Series[T](
                timestamps=(),
                values=(),
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

        max_value = max(self.values)
        return Series[T](
            timestamps=(self.timestamps[0],) if self.timestamps else (),
            values=(max_value,),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def min(self, field: str | None = None) -> Series[T]:
        """Minimum value in series.

        Args:
            field: Optional field name (for future use with structured data).

        Returns:
            Series with a single value representing the minimum.
        """
        if len(self.values) == 0:
            return Series[T](
                timestamps=(),
                values=(),
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

        min_value = min(self.values)
        return Series[T](
            timestamps=(self.timestamps[0],) if self.timestamps else (),
            values=(min_value,),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def shift(self, periods: int) -> Series[T]:
        """Shift series values by a number of periods.

        Args:
            periods: Number of periods to shift (positive = forward, negative = backward).

        Returns:
            New series with shifted values. For forward shifts, earlier positions are filled
            with the first value. For backward shifts, later positions are filled with the last value.
        """
        if periods == 0:
            return Series[T](
                timestamps=self.timestamps,
                values=self.values,
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

        if len(self.values) == 0:
            return Series[T](
                timestamps=self.timestamps,
                values=self.values,
                symbol=self.symbol,
                timeframe=self.timeframe,
                availability_mask=self.availability_mask,
            )

        shifted_values: list[T] = list(self.values)
        if periods > 0:
            # Shift forward: move values to later timestamps
            if periods < len(shifted_values):
                shifted_values = [shifted_values[0]] * periods + shifted_values[:-periods]
            else:
                shifted_values = [shifted_values[0]] * len(shifted_values)
        else:
            # Shift backward: move values to earlier timestamps
            periods_abs = abs(periods)
            if periods_abs < len(shifted_values):
                shifted_values = shifted_values[periods_abs:] + [shifted_values[-1]] * periods_abs
            else:
                shifted_values = [shifted_values[-1]] * len(shifted_values)

        return Series[T](
            timestamps=self.timestamps,
            values=tuple(shifted_values),
            symbol=self.symbol,
            timeframe=self.timeframe,
            availability_mask=self.availability_mask,
        )

    def change(self, periods: int = 1) -> Series[float]:
        """Calculate absolute change from previous period(s).

        Args:
            periods: Number of periods to look back (default: 1).

        Returns:
            Series with change values. First 'periods' values will be None/NaN.
        """
        from decimal import Decimal

        if len(self.values) < periods + 1:
            return Series[float](
                timestamps=self.timestamps,
                values=tuple([float("nan")] * len(self.values)),
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

        change_values: list[float] = []
        for i in range(len(self.values)):
            if i < periods:
                change_values.append(float("nan"))
            else:
                current = (
                    float(Decimal(str(self.values[i])))
                    if not isinstance(self.values[i], int | float | Decimal)
                    else float(self.values[i])
                )
                previous = (
                    float(Decimal(str(self.values[i - periods])))
                    if not isinstance(self.values[i - periods], int | float | Decimal)
                    else float(self.values[i - periods])
                )
                change_values.append(current - previous)

        return Series[float](
            timestamps=self.timestamps,
            values=tuple(change_values),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def change_pct(self, periods: int = 1) -> Series[float]:
        """Calculate percentage change from previous period(s).

        Args:
            periods: Number of periods to look back (default: 1).

        Returns:
            Series with percentage change values. First 'periods' values will be None/NaN.
        """
        from decimal import Decimal

        if len(self.values) < periods + 1:
            return Series[float](
                timestamps=self.timestamps,
                values=tuple([float("nan")] * len(self.values)),
                symbol=self.symbol,
                timeframe=self.timeframe,
            )

        change_pct_values: list[float] = []
        for i in range(len(self.values)):
            if i < periods:
                change_pct_values.append(float("nan"))
            else:
                current = (
                    float(Decimal(str(self.values[i])))
                    if not isinstance(self.values[i], int | float | Decimal)
                    else float(self.values[i])
                )
                previous = (
                    float(Decimal(str(self.values[i - periods])))
                    if not isinstance(self.values[i - periods], int | float | Decimal)
                    else float(self.values[i - periods])
                )
                if previous == 0:
                    change_pct_values.append(float("nan"))
                else:
                    change_pct_values.append((current - previous) / previous * 100.0)

        return Series[float](
            timestamps=self.timestamps,
            values=tuple(change_pct_values),
            symbol=self.symbol,
            timeframe=self.timeframe,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert series to dictionary format."""
        return {
            "timestamps": [ts.isoformat() for ts in self.timestamps],
            "values": list(self.values),
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "availability_mask": list(self.availability_mask) if self.availability_mask is not None else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Series[T]:
        """Create series from dictionary format."""
        from .timestamps import coerce_timestamp

        timestamps = tuple(coerce_timestamp(ts) for ts in data["timestamps"])
        values = tuple(data["values"])

        return cls(
            timestamps=timestamps,
            values=values,
            symbol=data["symbol"],
            timeframe=data["timeframe"],
            availability_mask=(tuple(data["availability_mask"]) if data.get("availability_mask") is not None else None),
        )

    def _validate_series_alignment(self, other: Series[Any], *, operation: str) -> None:
        """Ensure two series are aligned before performing arithmetic."""
        if self.symbol != other.symbol or self.timeframe != other.timeframe:
            raise ValueError(
                f"Cannot {operation} series with different symbols or timeframes: "
                f"({self.symbol},{self.timeframe}) vs ({other.symbol},{other.timeframe})"
            )
        if len(self) != len(other):
            raise ValueError(f"Cannot {operation} series with different lengths: {len(self)} vs {len(other)}")
        if self.timestamps != other.timestamps:
            raise ValueError(f"Cannot {operation} series with different timestamp alignment")


def _and_masks(a: tuple[bool, ...] | None, b: tuple[bool, ...] | None) -> tuple[bool, ...] | None:
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    if len(a) != len(b):
        raise ValueError("Cannot combine availability masks of different lengths")
    return tuple(x and y for x, y in zip(a, b, strict=False))


# Type aliases for common series types
PriceSeries: TypeAlias = Series[Price]
QtySeries: TypeAlias = Series[Qty]


def align_series(
    left: Series[Any],
    right: Series[Any],
    *,
    how: Literal["inner", "outer", "left", "right"] = "inner",
    fill: Literal["none", "ffill"] = "none",
    left_fill_value: Any | None = None,
    right_fill_value: Any | None = None,
    symbol: Symbol | None = None,
    timeframe: str | None = None,
) -> tuple[Series[Any], Series[Any]]:
    """Align two series to a common timestamp set with explicit strategy.

    Args:
        left: First series.
        right: Second series.
        how: Join strategy ("inner", "outer", "left", "right").
        fill: Gap handling strategy. "none" raises on missing values, "ffill" propagates
              the last observed value (optionally seeded with fill_value parameters).
        left_fill_value: Seed value for left series when fill="ffill" and no prior value exists.
        right_fill_value: Seed value for right series when fill="ffill" and no prior value exists.
        symbol: Output symbol metadata. If omitted, requires both series to share symbol.
        timeframe: Output timeframe metadata. If omitted, requires both series to share timeframe.

    Returns:
        Tuple of aligned Series instances sharing metadata (symbol/timeframe).

    Raises:
        ValueError: If metadata differs without overrides, timestamps cannot be combined
                    under the chosen strategy, or missing values cannot be filled.
    """

    supported_how = {"inner", "outer", "left", "right"}
    if how not in supported_how:
        raise ValueError(f"Unsupported alignment strategy '{how}'. Expected one of {supported_how}.")

    if symbol is None:
        if left.symbol != right.symbol:
            raise ValueError("Series have different symbols; provide 'symbol' to align under a common identifier.")
        target_symbol = left.symbol
    else:
        target_symbol = symbol

    if timeframe is None:
        if left.timeframe != right.timeframe:
            raise ValueError("Series have different timeframes; provide 'timeframe' to align under a common timeframe.")
        target_timeframe = left.timeframe
    else:
        target_timeframe = timeframe

    left_ts = set(left.timestamps)
    right_ts = set(right.timestamps)

    if how == "inner":
        target_ts = sorted(left_ts & right_ts)
    elif how == "outer":
        target_ts = sorted(left_ts | right_ts)
    elif how == "left":
        target_ts = list(left.timestamps)
    else:  # how == "right"
        target_ts = list(right.timestamps)

    if not target_ts:
        raise ValueError("Alignment resulted in an empty timestamp set.")

    def build_values(series: Series[Any], timestamps: list[Timestamp], fill_value: Any | None) -> tuple[Any, ...]:
        values_map = dict(zip(series.timestamps, series.values, strict=False))
        new_values: list[Any] = []
        last_value: Any | None = None

        for ts in timestamps:
            if ts in values_map:
                value = values_map[ts]
                last_value = value
            else:
                if fill == "ffill":
                    if last_value is not None:
                        value = last_value
                    elif fill_value is not None:
                        value = fill_value
                        last_value = value
                    else:
                        raise ValueError(
                            f"Missing value for timestamp {ts.isoformat()} in series '{series.symbol}' "
                            "and no forward-fill seed provided."
                        )
                else:
                    raise ValueError(
                        f"Missing value for timestamp {ts.isoformat()} in series '{series.symbol}'. "
                        "Specify fill='ffill' or provide fill values."
                    )
            new_values.append(value)
        return tuple(new_values)

    aligned_left_values = build_values(left, target_ts, left_fill_value)
    aligned_right_values = build_values(right, target_ts, right_fill_value)

    def build_mask(series: Series[Any], timestamps: list[Timestamp]) -> tuple[bool, ...] | None:
        if series.availability_mask is None:
            return None
        index_map = {ts: i for i, ts in enumerate(series.timestamps)}
        out: list[bool] = []
        for ts in timestamps:
            if ts in index_map:
                out.append(series.availability_mask[index_map[ts]])
            else:
                # Filled via join; consider available
                out.append(True)
        return tuple(out)

    aligned_left = Series[Any](
        timestamps=tuple(target_ts),
        values=aligned_left_values,
        symbol=target_symbol,
        timeframe=target_timeframe,
        availability_mask=build_mask(left, target_ts),
    )
    aligned_right = Series[Any](
        timestamps=tuple(target_ts),
        values=aligned_right_values,
        symbol=target_symbol,
        timeframe=target_timeframe,
        availability_mask=build_mask(right, target_ts),
    )

    return aligned_left, aligned_right
