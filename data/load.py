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
    """Solve a Sudoku puzzle using Z3 and return solution as a string of 81 digits."""
    grid = [[int(sudoku_str[i*9 + j]) for j in range(9)] for i in range(9)]
    solver = Solver()
    cells = [[Int(f"cell_{i}_{j}") for j in range(9)] for i in range(9)]

    for i in range(9):
        for j in range(9):
            solver.add(cells[i][j] >= 1, cells[i][j] <= 9)

    for i in range(9):
        for j in range(9):
            if grid[i][j] != 0:
                solver.add(cells[i][j] == grid[i][j])

    for i in range(9):
        solver.add(Distinct(cells[i]))  # fila
        solver.add(Distinct([cells[j][i] for j in range(9)]))  # columna

    for box_i in range(3):
        for box_j in range(3):
            block = [cells[box_i*3 + i][box_j*3 + j] for i in range(3) for j in range(3)]
            solver.add(Distinct(block))

    if solver.check() == sat:
        model = solver.model()
        solution = ''.join(str(model.evaluate(cells[i][j])) for i in range(9) for j in range(9))
        print("Solved Sudoku:", solution)
        return solution
    else:
        return None


def is_valid_sudoku_solution(sudoku_string: str) -> bool:
    """
    Check if a string of 81 digits represents a valid Sudoku solution.

    Args:
        sudoku_string: A string of 81 digits, '0' should not appear in a valid solution.

    Returns:
        True if the string is a valid Sudoku solution, False otherwise.
    """
    if len(sudoku_string) != 81 or not sudoku_string.isdigit() or '0' in sudoku_string:
        return False

    grid = [[int(sudoku_string[i*9 + j]) for j in range(9)] for i in range(9)]

    # Check rows
    for row in grid:
        if len(set(row)) != 9:
            return False

    # Check columns
    for col in range(9):
        if len(set(grid[row][col] for row in range(9))) != 9:
            return False

    # Check 3x3 blocks
    for box_i in range(3):
        for box_j in range(3):
            block = [grid[box_i*3 + i][box_j*3 + j] for i in range(3) for j in range(3)]
            if len(set(block)) != 9:
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
