import sys
import os
import csv
import time
import threading
import warnings
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dotenv import load_dotenv

load_dotenv()

# Suppress aiohttp warnings
warnings.filterwarnings("ignore", message=".*Unclosed.*")
warnings.filterwarnings("ignore", category=ResourceWarning)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from sudoku.data.load import format_sudoku, is_valid_sudoku_solution
from sudoku.tools.sudoku import solve_sudoku_tool, show_sudoku,validate_sudoku_solution
from strands.models.gemini import GeminiModel


# Configuration
MAX_TIMEOUT_MINUTES = 5
CSV_INPUT_PATH = "../data/sudokus_9x9.csv"
RESULTS_OUTPUT_PATH = "results_9_agent.txt"

def remove_think_tags(text):
    """Remove <think> and </think> tags and their content from the text."""
    import re
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def solve_sudoku_with_timeout(agent, puzzle, timeout_seconds):
    result = [None]
    exception = [None]
    
    def solve_task():
        try:
            result[0] = agent(f"Can you solve this {len(puzzle)}-digit sudoku?: {puzzle}")
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


# Pydantic model defining the expected JSON output
class SudokuResult(BaseModel):
    """Model that contains the base information of Sudoku Solution which is the sudoku and the solution as 16 or 81 digit strings."""
    sudoku: str = Field(description="Original Sudoku puzzle string as an 16 or 81-digit string")
    solution: str = Field(description="Solved Sudoku as an 16 or 81-digit string")


# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  
    model_id="qwen3:1.7b",
    temperature=0.1              
)


SYSTEM_PROMPT = """
You are a Sudoku-solving agent. You have access to tools that can help you solve and validate Sudoku puzzles. Always use the tools and never validate yourself your solutions.
You have access to the tools `show_sudoku`, `solve_sudoku_tool`, and `validate_sudoku_solution`.

IMPORTANT: Your response must be a JSON object with exactly the following format and nothing else:
{
    "sudoku": "<the original 81-digit puzzle string>",
    "solution": "<the 81-digit solution string>"
}

Instructions:
1. When a user provides a Sudoku puzzle as a string of 81 digits (0 represents empty cells):
   a. Call `solve_sudoku_tool` to solve the puzzle.
   b. Call `validate_sudoku_solution` with the output to ensure it is valid.
   c. Do NOT attempt to solve, format, or validate the Sudoku yourself; rely only on the tools.
2. Return a JSON following the exact schema above.
"""

# Create an agent using the Ollama model and both tools


SYSTEM_PROMPT_FORMATTER = """
You are a formatting agent that will return a structured output as a SudokuResult object.
Never try to validate solution or solve the sudoku yourself, just return the answer as a SudokuResult object.
Extract puzzle and solution from the response. Return SudokuResult with:
- sudoku: original 81-digit string
- solution: solved 81-digit string
"""



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
            
            agent = Agent(
                model=ollama_model,
                system_prompt=SYSTEM_PROMPT,
                callback_handler=None,
                tools=[solve_sudoku_tool, show_sudoku,validate_sudoku_solution]
            )

            structured_output_agent = Agent(
                model=ollama_model,
                system_prompt=SYSTEM_PROMPT_FORMATTER,
                callback_handler=None,
            )
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
                    'solve_time': round(solve_time,2),
                    'status': 'timeout'
                })
            else:
                try:
                    print("\nFormating solution...")
                    cleaned_result = remove_think_tags(str(result))
                    print("Cleaned output = ", str(cleaned_result))
                    result = structured_output_agent(
                        f"Format this sudoku solution: {cleaned_result}",
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
    print(f"Average time to solve Sudoku: {sum([r['solve_time'] for r in results if r['status'] == 'solved'])/solved_puzzles:.2f}s")
    print(f"Results saved to: {RESULTS_OUTPUT_PATH}")

if __name__ == "__main__":
    try:
        process_sudokus()
    except KeyboardInterrupt:
        print("\nExecution interrupted by user (Ctrl+C). Exiting immediately.")
    except Exception as e:
        print(f"Error during execution: {e}")