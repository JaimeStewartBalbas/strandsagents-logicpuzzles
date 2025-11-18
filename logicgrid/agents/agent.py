import sys
import os
import json
import time
import threading
import warnings
import csv
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
from logicgrid.tools.tools import solve_logic_grid_tool
from logicgrid.tools.solvers import check_solution
from strands.models.gemini import GeminiModel

# Configuration
MAX_TIMEOUT_MINUTES = 5
JSONL_INPUT_PATH = "../data/logic_puzzles_auto.jsonl"
RESULTS_OUTPUT_PATH = "results_logicgrid_agent.txt"

def remove_think_tags(text):
    """Remove <think> and </think> tags and their content from the text."""
    import re
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

def solve_logic_grid_with_timeout(agent, puzzle_text, timeout_seconds):
    result = [None]
    exception = [None]
    
    def solve_task():
        try:
            result[0] = agent(f"Please solve this logic grid puzzle: {puzzle_text}")
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

# Pydantic model for structured output
class LogicGridResult(BaseModel):
    """Model for logic grid puzzle solution."""
    solution: dict = Field(description="Solution as nested dict {entity: {attr: value}}")

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  
    model_id="qwen3:1.7b",
    temperature=0.1              
)

SYSTEM_PROMPT = """
You are a logic grid puzzle solver. Use solve_logic_grid_tool to solve puzzles.

Steps:
1. Extract entities (people names)
2. Extract attributes (categories and values)
3. Convert clues:
   - "X has Y" → {"type": "eq", "entity": "X", "attr": "category", "value": "Y"}
   - "X doesn't have Y" → {"type": "neq", "entity": "X", "attr": "category", "value": "Y"}
   - "Whoever has A has B" → {"type": "cross_eq", "attr1": "cat1", "value1": "A", "attr2": "cat2", "value2": "B"}
   - "Person with A doesn't have B" → {"type": "cross_neq", "attr1": "cat1", "value1": "A", "attr2": "cat2", "value2": "B"}
4. Call solve_logic_grid_tool(entities, attributes, clues)
5. Return only the solution JSON

Always use the tool - never solve manually.

IMPORTANT: Your response must be a JSON object with exactly the following format and nothing else:
{
    "solution": {"Person1": {"attr1": "value1", "attr2": "value2"}, "Person2": {...}, ...}
}
"""

SYSTEM_PROMPT_FORMATTER = """
You are a formatting agent that extracts logic grid solutions.
Extract the solution from the response and return as LogicGridResult.
Solution format: {"Person1": {"attr1": "value1", "attr2": "value2"}, ...}
"""

if __name__ == "__main__":
    results = []
    total_puzzles = 0
    solved_puzzles = 0
    timeout_puzzles = 0
    
    with open(JSONL_INPUT_PATH, 'r') as file:
        for line in file:
            if line.strip():
                puzzle_data = json.loads(line)
                total_puzzles += 1
                
                print(f"\nProcessing puzzle {total_puzzles}: {puzzle_data['id']}")
                
                agent = Agent(
                    model=ollama_model,
                    system_prompt=SYSTEM_PROMPT,
                    callback_handler=None,
                    tools=[solve_logic_grid_tool]
                )

                structured_output_agent = Agent(
                    model=ollama_model,
                    system_prompt=SYSTEM_PROMPT_FORMATTER,
                    callback_handler=None,
                )
                
                start_time = time.time()
                result = solve_logic_grid_with_timeout(agent, puzzle_data['text_prompt'], MAX_TIMEOUT_MINUTES * 60)
                end_time = time.time()
                solve_time = end_time - start_time
                
                if result is None:
                    print(f"Timeout or error for puzzle {total_puzzles}")
                    timeout_puzzles += 1
                    results.append({
                        'puzzle_id': puzzle_data['id'],
                        'expected_solution': puzzle_data['solution'],
                        'agent_solution': None,
                        'is_correct': False,
                        'solve_time': round(solve_time, 2),
                        'status': 'timeout'
                    })
                else:
                    try:
                        cleaned_result = remove_think_tags(str(result))
                        formatted_result = structured_output_agent(
                            f"Extract the logic grid solution: {cleaned_result}",
                            structured_output_model=LogicGridResult,
                        )
                        
                        structured_result = formatted_result.structured_output
                        agent_solution = structured_result.solution
                        expected_solution = puzzle_data['solution']
                        
                        is_correct = check_solution(expected_solution, agent_solution)
                        
                        if is_correct:
                            solved_puzzles += 1
                            print(f"✓ Correct solution in {solve_time:.2f}s")
                        else:
                            print(f"✗ Incorrect solution in {solve_time:.2f}s")
                        
                        results.append({
                            'puzzle_id': puzzle_data['id'],
                            'expected_solution': expected_solution,
                            'agent_solution': agent_solution,
                            'is_correct': is_correct,
                            'solve_time': round(solve_time, 2),
                            'status': 'solved'
                        })
                        
                    except Exception as e:
                        print(f"Error formatting result: {e}")
                        results.append({
                            'puzzle_id': puzzle_data['id'],
                            'expected_solution': puzzle_data['solution'],
                            'agent_solution': None,
                            'is_correct': False,
                            'solve_time': round(solve_time, 2),
                            'status': 'error'
                        })
    
    with open(RESULTS_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['puzzle_id', 'expected_solution', 'agent_solution', 'is_correct', 'solve_time', 'status']
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
