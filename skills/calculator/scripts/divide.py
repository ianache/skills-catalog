"""Calculator tool implementations for Google ADK."""

from typing import Dict, Any


def execute(a: float, b: float) -> Dict[str, Any]:
    """Divide first number by second.
    
    Args:
        a: Dividend (first number)
        b: Divisor (second number)
        
    Returns:
        Dictionary with result and operation details
        
    Raises:
        ValueError: If divisor is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    
    result = a / b
    return {
        "result": result,
        "operation": "divide",
        "expression": f"{a} / {b} = {result}"
    }
