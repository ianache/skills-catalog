"""Calculator tool implementations for Google ADK."""

from typing import Dict, Any


def execute(a: float, b: float) -> Dict[str, Any]:
    """Subtract second number from first.
    
    Args:
        a: First number (minuend)
        b: Second number (subtrahend)
        
    Returns:
        Dictionary with result and operation details
    """
    result = a - b
    return {
        "result": result,
        "operation": "subtract",
        "expression": f"{a} - {b} = {result}"
    }
