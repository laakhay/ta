"""Expression compilation pipeline."""

from .ir.nodes import CanonicalExpression
from .dsl.parser import ExpressionParser
from .normalize.normalize import normalize_expression
from .typecheck.checker import typecheck_expression

def compile_to_ir(expression_text: str) -> CanonicalExpression:
    """Compile an expression string into a verified Canonical IR.
    
    Pipeline:
    1. Parse text into raw IR (using ExpressionParser).
    2. Normalize IR (alias expansion, canonical args).
    3. Typecheck IR (static type safety).
    
    Args:
        expression_text: The user's expression string.
        
    Returns:
        The fully canonicalized, verified CanonicalExpression.
    """
    parser = ExpressionParser()
    raw_ir = parser.parse_text(expression_text)
    normalized_ir = normalize_expression(raw_ir)
    typechecked_ir = typecheck_expression(normalized_ir)
    return typechecked_ir
