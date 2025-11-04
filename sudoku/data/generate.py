import csv
from sudoku import Sudoku
import random

def generate_4x4_sudokus(filename="sudokus_4x4.csv", n=10, difficulty=0.5):
    """
    Genera n sudokus 4x4 diferentes usando pysudoku con seeds distintas.
    Guarda en CSV en formato string plano (0 para casillas vacías).
    """
    sudokus = []

    for _ in range(n):
        seed = random.randint(1,100_000_000)
        print("Using seed:", seed)
        puzzle = Sudoku(2, seed=seed).difficulty(difficulty)

        print("Puzzle:")
        print(puzzle.board)
        # Convertir puzzle y solución en strings planos
        puzzle_str = "".join(str(cell or 0) for row in puzzle.board for cell in row)
        solution_str = "".join(str(cell or 0) for row in puzzle.solve().board for cell in row)

        sudokus.append((puzzle_str, solution_str))

    # Guardar en CSV
    with open(filename, mode="w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sudoku", "solution"])
        writer.writerows(sudokus)

    print(f" Generados {n} sudokus 4x4 distintos y guardados en {filename}")
    
    
if __name__ == "__main__":
    generate_4x4_sudokus("./data/sudokus_4x4.csv", n=10, difficulty=0.5)
