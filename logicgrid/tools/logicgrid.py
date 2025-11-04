from strands import tool
from data.load import solve_logic_grid_puzzle, format_logic_grid_puzzle, validate_logic_grid_solution
import json
from typing import Dict, Any

@tool
def solve_logic_grid_tool(puzzle: str) -> str:
    """Solve a logic grid puzzle.

    Args:
        puzzle: A JSON string or text containing the logic grid puzzle data.

    Returns:
        A string containing the solution of the logic grid puzzle.
    """
    try:
        if puzzle.startswith('{'):
            puzzle_data = json.loads(puzzle)
        else:
            puzzle_data = {"problem": puzzle}
        
        solution = solve_logic_grid_puzzle(puzzle_data)
        return f"The solution of the logic grid puzzle is: {solution}"
    except Exception as e:
        return f"Error solving puzzle: {str(e)}"

@tool
def show_logic_grid(puzzle_data: str) -> str:
    """
    Display a logic grid puzzle in a readable format.

    This tool takes puzzle data and formats it for human readability.

    Args:
        puzzle_data: JSON string or text containing the puzzle information
    
    Returns:
        Formatted puzzle display
    """
    try:
        if puzzle_data.startswith('{'):
            data = json.loads(puzzle_data)
        else:
            data = {"problem": puzzle_data}
        
        formatted = format_logic_grid_puzzle(data)
        return f"Formatted logic grid puzzle:\n{formatted}"
    except Exception as e:
        return f"Error formatting puzzle: {str(e)}"

@tool
def validate_logic_grid_solution_tool(puzzle: str, solution: str) -> str:
    """
    Check if a given logic grid puzzle solution is valid.

    Args:
        puzzle: JSON string or text containing the original puzzle
        solution: The proposed solution to validate

    Returns:
        A message indicating if the solution is valid or not.
    """
    try:
        if puzzle.startswith('{'):
            puzzle_data = json.loads(puzzle)
        else:
            puzzle_data = {"problem": puzzle}
        
        is_valid = validate_logic_grid_solution(puzzle_data, solution)
        
        if is_valid:
            return "The provided logic grid solution is valid."
        else:
            return "The provided logic grid solution is NOT valid."
    except Exception as e:
        return f"Error validating solution: {str(e)}"