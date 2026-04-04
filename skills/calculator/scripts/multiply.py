"""Calculator tool implementations for Google ADK."""

from typing import Dict, Any


def execute(a: float, b: float) -> Dict[str, Any]:
    """Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Dictionary with result and operation details
    """
    result = a * b
    return {
        "result": result,
        "operation": "multiply",
        "expression": f"{a} * {b} = {result}"
    }
