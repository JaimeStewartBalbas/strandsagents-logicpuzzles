from strands import tool
from data.load import solve_sudoku, format_sudoku, is_valid_sudoku_solution

@tool
def solve_sudoku_tool(sudoku: str) -> str:
    """Solve a Sudoku puzzle.

    Args:
        sudoku: A string of 81 digits (0 for empty cells).

    Returns:
        A string containing the solution of the sudoku 81 digits representing the solved Sudoku.
    """
    
    return f"The solution of the sudoku {sudoku} is {solve_sudoku(sudoku)}"


@tool
def show_sudoku(sudoku_string: str):
    """
    Display a Sudoku puzzle in a readable format.

    This tool takes a string of exactly 81 digits, where '0' represents an empty cell,
    and prints the Sudoku grid in a human-readable format.

    Example of usage:
    show_sudoku("004300209005009001070060043006002087190007400050083000600000105003508690042910300")
    """
    return f"Formatting sudoku: {sudoku_string} to {format_sudoku(sudoku_string)}"


from data.load import is_valid_sudoku_solution  # ajusta la ruta según tu proyecto

@tool
def validate_sudoku_solution(sudoku_string: str) -> str:
    """
    Check if a given Sudoku solution string is valid.

    Args:
        sudoku_string: A string of 81 digits representing a Sudoku solution.

    Example usage:
        validate_sudoku_solution("400053270020600803008904010145200006000048300000001090601300450000070900780000060")

    Returns:
        A friendly message indicating if the solution is valid or not.
    """
    if is_valid_sudoku_solution(sudoku_string):
        return "The provided Sudoku string is a valid solution."
    else:
        return "The provided Sudoku string is NOT a valid solution."