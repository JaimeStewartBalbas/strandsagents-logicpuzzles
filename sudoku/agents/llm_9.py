import sys
import os
import csv
import time
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, TimeoutError

# Suppress aiohttp warnings
warnings.filterwarnings("ignore", message=".*Unclosed.*")
warnings.filterwarnings("ignore", category=ResourceWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from sudoku.data.load import format_sudoku, is_valid_sudoku_solution
from strands.models.gemini import GeminiModel

# Configuration
MAX_TIMEOUT_MINUTES = 10
CSV_INPUT_PATH = "../data/sudoku_sample.csv"
RESULTS_OUTPUT_PATH = "results.txt"

def solve_sudoku_with_timeout(agent, puzzle, timeout_seconds):
    result = [None]
    exception = [None]
    
    def solve_task():
        try:
            result[0] = agent(f"Can you solve this sudoku?: {puzzle}")
        except Exception as e:
            exception[0] = e
    
    thread = threading.Thread(target=solve_task, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    
    if thread.is_alive():
        print(f"Timeout reached ({timeout_seconds}s), stopping inference...")
        return None
    
    if exception[0]:
        print(f"Error solving puzzle: {exception[0]}")
        return None
        
    return result[0]

class SudokuResult(BaseModel):
    sudoku: str = Field(description="Original Sudoku puzzle as a 81-digit string")
    solution: str = Field(description="Solved Sudoku as a 81-digit string")

ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3:14b",
)

gemini_model = GeminiModel(
    client_args={
        "api_key": os.getenv("GEMINI_API_KEY"),
    },
    # **model_config
    model_id="gemini-2.5-pro",
)

SYSTEM_PROMPT = """
You are a Sudoku-solving assistant.
You will receive a flattened 9x9 Sudoku puzzle as a string of 81 digits (0 represents empty cells).
Solve the puzzle using your reasoning capabilities quickly.

IMPORTANT: Your response must be a JSON object **exactly** in this format and nothing else:

{
    "sudoku": "<the original 81-digit puzzle string>",
    "solution": "<the 81-digit solution string>"
}

Return **only the JSON object**.
"""

agent = Agent(
    model=gemini_model,
    system_prompt=SYSTEM_PROMPT,
    #callback_handler=None,
)

structured_output_agent = Agent(
    model=gemini_model,
    system_prompt="Format the Sudoku solution as SudokuResult object.",
    callback_handler=None,
)

def process_sudokus():
    results = []
    total_puzzles = 0
    solved_puzzles = 0
    timeout_puzzles = 0
    
    with open(CSV_INPUT_PATH, 'r') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            puzzle = row['sudoku']
            expected_solution = row['solution']
            total_puzzles += 1
            
            print(f"\nProcessing puzzle {total_puzzles}: {puzzle}")
            
            start_time = time.time()
            result = solve_sudoku_with_timeout(agent, puzzle, MAX_TIMEOUT_MINUTES * 60)
            end_time = time.time()
            solve_time = end_time - start_time
            
            if result is None:
                print(f"Timeout or error for puzzle {total_puzzles}")
                timeout_puzzles += 1
                results.append({
                    'puzzle': puzzle,
                    'expected_solution': expected_solution,
                    'agent_solution': None,
                    'is_correct': False,
                    'solve_time': solve_time,
                    'status': 'timeout'
                })
            else:
                try:
                    print("Formating solution...")
                    result = structured_output_agent(
                        f"Format this sudoku solution: {result}",
                        structured_output_model=SudokuResult,
                    )
                    
                    structured_result = result.structured_output
                    agent_solution = structured_result.solution
                    print("Agent proposed solution: ", agent_solution)
                    is_correct = agent_solution == expected_solution
                    print("Actual solution: ", expected_solution)

                    if is_correct or is_valid_sudoku_solution(agent_solution):
                        solved_puzzles += 1
                        print(f"✓ Correct solution in {solve_time:.2f}s")
                    else:
                        print(f"✗ Incorrect solution in {solve_time:.2f}s")
                    
                    results.append({
                        'puzzle': puzzle,
                        'expected_solution': expected_solution,
                        'agent_solution': agent_solution,
                        'is_correct': is_correct,
                        'solve_time': solve_time,
                        'status': 'solved'
                    })
                    
                except Exception as e:
                    print(f"Error formatting result: {e}")
                    results.append({
                        'puzzle': puzzle,
                        'expected_solution': expected_solution,
                        'agent_solution': None,
                        'is_correct': False,
                        'solve_time': solve_time,
                        'status': 'error'
                    })
    
    with open(RESULTS_OUTPUT_PATH, 'w', newline='') as file:
        fieldnames = ['puzzle', 'expected_solution', 'agent_solution', 'is_correct', 'solve_time', 'status']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n=== STATISTICS ===")
    print(f"Total puzzles: {total_puzzles}")
    print(f"Solved correctly: {solved_puzzles}")
    print(f"Timeouts/Errors: {timeout_puzzles}")
    print(f"Success rate: {(solved_puzzles/total_puzzles)*100:.1f}%")
    print(f"Results saved to: {RESULTS_OUTPUT_PATH}")

if __name__ == "__main__":
    try:
        process_sudokus()
    except KeyboardInterrupt:
        print("\nExecution interrupted by user (Ctrl+C). Exiting immediately.")
    except Exception as e:
        print(f"Error during execution: {e}")