import numpy as np
from z3 import Solver, Int, Distinct, sat
import csv

FILE_PATH = 'sudoku.csv'
OUTPUT_PATH = 'sudoku_sample.csv'

def format_sudoku(sudoku_string: str) -> str:
    """
    Return a Sudoku puzzle as a formatted string.
    Supports:
      - 9x9 puzzles (81 digits)
      - 4x4 puzzles (16 digits)
    '0' represents empty cells.
    """
    length = len(sudoku_string)

    if length == 81:  # 9x9 Sudoku
        size = 9
        box = 3
        line = "+-------+-------+-------+\n"
    elif length == 16:  # 4x4 Sudoku
        size = 4
        box = 2
        line = "+-----+-----+\n"
    else:
        raise ValueError("El Sudoku debe tener 81 (9x9) o 16 (4x4) dígitos")

    output = line
    for i in range(size):
        row = ""
        for j in range(size):
            val = sudoku_string[i * size + j]
            val = val if val != '0' else '.'
            if j % box == 0:
                row += "| "
            row += val + " "
        row += "|\n"
        output += row
        if (i + 1) % box == 0:
            output += line
    return output

def solve_sudoku(sudoku_str):
    """Solve a Sudoku puzzle using Z3. Supports 4x4 and 9x9 puzzles."""
    length = len(sudoku_str)
    
    if length == 81:  # 9x9 Sudoku
        size = 9
        box_size = 3
    elif length == 16:  # 4x4 Sudoku
        size = 4
        box_size = 2
    else:
        raise ValueError("Sudoku must have 16 (4x4) or 81 (9x9) digits")
    
    grid = [[int(sudoku_str[i*size + j]) for j in range(size)] for i in range(size)]
    solver = Solver()
    cells = [[Int(f"cell_{i}_{j}") for j in range(size)] for i in range(size)]

    for i in range(size):
        for j in range(size):
            solver.add(cells[i][j] >= 1, cells[i][j] <= size)

    for i in range(size):
        for j in range(size):
            if grid[i][j] != 0:
                solver.add(cells[i][j] == grid[i][j])

    for i in range(size):
        solver.add(Distinct(cells[i]))  # row
        solver.add(Distinct([cells[j][i] for j in range(size)]))  # column

    for box_i in range(box_size):
        for box_j in range(box_size):
            block = [cells[box_i*box_size + i][box_j*box_size + j] for i in range(box_size) for j in range(box_size)]
            solver.add(Distinct(block))

    if solver.check() == sat:
        model = solver.model()
        solution = ''.join(str(model.evaluate(cells[i][j])) for i in range(size) for j in range(size))
        return solution
    else:
        return None

def is_valid_sudoku_solution(sudoku_string: str) -> bool:
    """
    Check if a string represents a valid Sudoku solution. Supports 4x4 and 9x9.

    Args:
        sudoku_string: A string of 16 (4x4) or 81 (9x9) digits, '0' should not appear in a valid solution.

    Returns:
        True if the string is a valid Sudoku solution, False otherwise.
    """
    length = len(sudoku_string)
    
    if length == 81:  # 9x9 Sudoku
        size = 9
        box_size = 3
    elif length == 16:  # 4x4 Sudoku
        size = 4
        box_size = 2
    else:
        return False
    
    if not sudoku_string.isdigit() or '0' in sudoku_string:
        return False

    grid = [[int(sudoku_string[i*size + j]) for j in range(size)] for i in range(size)]

    # Check rows
    for row in grid:
        if len(set(row)) != size:
            return False

    # Check columns
    for col in range(size):
        if len(set(grid[row][col] for row in range(size))) != size:
            return False

    # Check blocks
    for box_i in range(box_size):
        for box_j in range(box_size):
            block = [grid[box_i*box_size + i][box_j*box_size + j] for i in range(box_size) for j in range(box_size)]
            if len(set(block)) != size:
                return False

    return True




# ---------------------------------
# Bloque que solo se ejecuta al correr el script directamente
# ---------------------------------
if __name__ == "__main__":

    # Arrays for just 10 puzzles
    quizzes = np.zeros((10, 81), np.int32)
    solutions = np.zeros((10, 81), np.int32)

    # Read only the first 10 lines (after header)
    with open(FILE_PATH, 'r') as f:
        lines = f.read().splitlines()[1:11]

    for i, line in enumerate(lines):
        quiz, solution = line.split(",")
        for j, (q, s) in enumerate(zip(quiz, solution)):
            quizzes[i, j] = int(q)
            solutions[i, j] = int(s)

    quizzes = quizzes.reshape((-1, 9, 9))
    solutions = solutions.reshape((-1, 9, 9))

    print("First Sudoku Puzzle:")
    print_sudoku(quizzes[0].flatten().astype(str))
    print("\n")

    print("Solving the first Sudoku with Z3...")
    solution_solver = solve_sudoku(quizzes[0].flatten().astype(str))
    print_sudoku(solution_solver)

    print("\n")
    print("First Sudoku Solution (Ground Truth):")
    print(len(solutions[0].flatten().astype(str)))
    print_sudoku(solutions[0].flatten().astype(str))

    # Save the 10 sudokus into a new CSV
    with open(OUTPUT_PATH, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["quizzes", "solutions"])  # header
        for q, s in zip(quizzes, solutions):
            writer.writerow([
                "".join(map(str, q.flatten())), 
                "".join(map(str, s.flatten()))
            ])

    print(f"Saved first 10 puzzles to {OUTPUT_PATH}")
