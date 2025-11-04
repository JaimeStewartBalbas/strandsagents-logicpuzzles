import csv
import json
import os
from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from typing import Dict, Any
from strands.handlers.callback_handler import PrintingCallbackHandler

# Define Pydantic model for structured output
class LogicGridSolution(BaseModel):
    puzzle_id: str = Field(description="ID of the puzzle")
    solution: Dict[str, Dict[str, str]] = Field(description="Complete solution mapping")

# Create Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3:4b"
)

# System prompt for logic grid puzzle solving
SYSTEM_PROMPT = """
Solve logic grid puzzles using logical reasoning.

Return ONLY JSON in this format:
{
    "puzzle_id": "<puzzle ID>",
    "solution": {
        "<person>": {
            "<category>": "<value>"
        }
    }
}

Example:
{
    "puzzle_id": "test_1",
    "solution": {
        "Ana": {"Pet": "Dog", "City": "Lima"},
        "Bob": {"Pet": "Cat", "City": "Paris"}
    }
}

Rules: Each person gets exactly one value per category. No explanations.
"""

# Create the agent
agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT,
    callback_handler=PrintingCallbackHandler(),
)

structured_output_agent = Agent(
    model=ollama_model,
    system_prompt="Convert the LLM response to the required LogicGridSolution format.",
    callback_handler=PrintingCallbackHandler(),
)

def load_puzzles_from_csv(csv_path: str = None) -> list:
    """
    Loads puzzles from the generated CSV file.
    """
    if csv_path is None:
        # Look for CSV in data directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_path = os.path.join(os.path.dirname(current_dir), "data", "generated_logic_puzzles.csv")
    
    puzzles = []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='$')
            for row in reader:
                puzzle = {
                    'puzzle_id': row['puzzle_id'],
                    'clue_count': int(row['clue_count']),
                    'llm_prompt': row['llm_prompt'],
                    'ground_truth_solution': json.loads(row['ground_truth_solution_json']),
                    'structured_clues': json.loads(row['structured_clues_json'])
                }
                puzzles.append(puzzle)
        
        print(f"Loaded {len(puzzles)} puzzles from {csv_path}")
        return puzzles
        
    except FileNotFoundError:
        print(f"Error: File not found {csv_path}")
        return []
    except Exception as e:
        print(f"Error loading puzzles: {e}")
        return []

def format_structured_clue(clue: Dict) -> str:
    """
    Converts a structured clue to natural language.
    """
    items = clue['items']
    clue_type = clue['type']
    
    if clue_type == 'positive':
        return f"{items[0]} is associated with {items[1]}"
    elif clue_type == 'negative':
        return f"{items[0]} is NOT associated with {items[1]}"
    elif clue_type == 'link':
        return f"{items[0]} and {items[1]} belong to the same person"
    else:
        return f"{clue_type}: {', '.join(items)}"

def solve_puzzle(puzzle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Solves an individual puzzle using the LLM agent.
    """
    structured_clues = puzzle_data['structured_clues']
    puzzle_id = puzzle_data['puzzle_id']
    
    # Create minimal prompt with only structured clues
    clues_text = "\n".join([f"{i+1}. {format_structured_clue(clue)}" for i, clue in enumerate(structured_clues)])
    full_prompt = f"Solve this logic grid puzzle:\n\nClues:\n{clues_text}\n\nPuzzle ID: {puzzle_id}"
    
    try:
        # Get LLM response
        print("="*10)
        print("\n\nInvocando con prompt : " + full_prompt + "\n\n")
        print("="*10)

        result = agent(full_prompt)
        
        # Try to parse as JSON
        if isinstance(result, str):
            # Clean response if it has extra text
            result = result.strip()
            if result.startswith('```json'):
                result = result[7:]
            if result.endswith('```'):
                result = result[:-3]
            result = result.strip()
            
            solution_json = json.loads(result)
        else:
            solution_json = result
        
        return {
            'puzzle_id': puzzle_id,
            'llm_solution': solution_json,
            'ground_truth': puzzle_data['ground_truth_solution'],
            'success': True,
            'error': None
        }
        
    except json.JSONDecodeError as e:
        return {
            'puzzle_id': puzzle_id,
            'llm_solution': None,
            'ground_truth': puzzle_data['ground_truth_solution'],
            'success': False,
            'error': f"Error parsing JSON: {e}",
            'raw_response': result
        }
    except Exception as e:
        return {
            'puzzle_id': puzzle_id,
            'llm_solution': None,
            'ground_truth': puzzle_data['ground_truth_solution'],
            'success': False,
            'error': f"Error during solving: {e}"
        }

def evaluate_solution(llm_solution: Dict, ground_truth: Dict) -> Dict[str, Any]:
    """
    Evaluates if the LLM solution matches the ground truth.
    """
    if not llm_solution or 'solution' not in llm_solution:
        return {'correct': False, 'reason': 'Invalid solution format'}
    
    llm_sol = llm_solution['solution']
    
    # Verify that all assignments match
    for person, assignments in ground_truth.items():
        if person not in llm_sol:
            return {'correct': False, 'reason': f'Missing person: {person}'}
        
        for category, value in assignments.items():
            if category not in llm_sol[person]:
                return {'correct': False, 'reason': f'Missing category {category} for {person}'}
            
            if llm_sol[person][category] != value:
                return {
                    'correct': False, 
                    'reason': f'Incorrect assignment: {person}->{category} should be {value}, got {llm_sol[person][category]}'
                }
    
    return {'correct': True, 'reason': 'Perfect match'}

if __name__ == "__main__":
    try:
        # Load puzzles from CSV
        puzzles = load_puzzles_from_csv()
        
        if not puzzles:
            print("Could not load puzzles. Exiting...")
            exit(1)
        
        print(f"\n=== SOLVING {len(puzzles)} LOGIC GRID PUZZLES ===")
        
        results = []
        correct_count = 0
        
        for i, puzzle in enumerate(puzzles, 1):
            if i == 1:
                print(f"\n--- Puzzle {i}/{len(puzzles)}: {puzzle['puzzle_id']} ---")
                print(f"Clues: {puzzle['clue_count']}")
                
                # Resolver puzzle
                result = solve_puzzle(puzzle)
                
                if result['success']:
                    # Evaluar solución
                    evaluation = evaluate_solution(result['llm_solution'], result['ground_truth'])
                    result['evaluation'] = evaluation
                    
                    if evaluation['correct']:
                        print("✅ CORRECT")
                        correct_count += 1
                    else:
                        print(f"❌ INCORRECT: {evaluation['reason']}")
                        print(f"LLM Solution: {result['llm_solution']}")
                        print(f"Correct Solution: {result['ground_truth']}")
                else:
                    print(f"❌ ERROR: {result['error']}")
                    if 'raw_response' in result:
                        print(f"Raw response: {result['raw_response'][:200]}...")
                
                results.append(result)
            
            # Resumen final
            print(f"\n=== FINAL SUMMARY ===")
            print(f"Puzzles solved correctly: {correct_count}/{len(puzzles)}")
            print(f"Success rate: {correct_count/len(puzzles)*100:.1f}%")
            
            # Mostrar errores si los hay
            errors = [r for r in results if not r['success']]
            if errors:
                print(f"\nErrors found ({len(errors)}):")
                for error in errors:
                    print(f"- {error['puzzle_id']}: {error['error']}")
            
            # Mostrar soluciones incorrectas
            incorrect = [r for r in results if r['success'] and not r['evaluation']['correct']]
            if incorrect:
                print(f"\nIncorrect solutions ({len(incorrect)}):")
                for inc in incorrect:
                    print(f"- {inc['puzzle_id']}: {inc['evaluation']['reason']}")
            
    except KeyboardInterrupt:
        print("\nExecution interrupted by user (Ctrl+C). Exiting...")
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()