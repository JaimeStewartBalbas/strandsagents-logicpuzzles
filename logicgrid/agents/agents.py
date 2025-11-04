from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from tools.logicgrid import solve_logic_grid_tool, show_logic_grid, validate_logic_grid_solution_tool
from data.load import format_logic_grid_puzzle, load_logic_grid_dataset

# Pydantic model defining the expected JSON output
class LogicGridResult(BaseModel):
    """Structured output for a solved logic grid puzzle."""
    puzzle: str = Field(description="Original logic grid puzzle")
    solution: str = Field(description="Solution to the logic grid puzzle")

# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  
    model_id="qwen3:8b"              
)

SYSTEM_PROMPT = """
You are a logic grid puzzle-solving agent. You have access to tools that can help you solve and validate logic grid puzzles.
You have access to the tools `show_logic_grid`, `solve_logic_grid_tool`, and `validate_logic_grid_solution_tool`.

IMPORTANT: Your response must be a JSON object with exactly the following format and nothing else:
{
    "puzzle": "<the original puzzle description>",
    "solution": "<the solution to the puzzle>"
}

Instructions:
1. When a user provides a logic grid puzzle:
   a. Call `show_logic_grid` to display the puzzle in a readable format.
   b. Call `solve_logic_grid_tool` to solve the puzzle.
   c. Call `validate_logic_grid_solution_tool` with the puzzle and solution to ensure it is valid.
      - If the solution is invalid, return a JSON with "solution": null.
   d. Do NOT attempt to solve or validate the puzzle yourself; rely only on the tools.
2. Return a JSON following the exact schema above.
"""

# Create an agent using the Ollama model and tools
agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT,
    tools=[solve_logic_grid_tool, show_logic_grid, validate_logic_grid_solution_tool]
)

SYSTEM_PROMPT_FORMATTER = """
You are a formatting assistant for logic grid puzzles.
You must format the logic grid puzzle solution provided by the input and return LogicGridResult object.
"""

structured_output_agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT_FORMATTER,
)

if __name__ == "__main__":
    # Load dataset and test with first example
    try:
        ds = load_logic_grid_dataset()
        
        if 'train' in ds and len(ds['train']) > 0:
            first_puzzle = ds['train'][0]
            print("Testing with first puzzle from dataset:")
            print(first_puzzle)
            
            # Convert to string for the agent
            puzzle_str = str(first_puzzle)
            
            # Use the agent to solve
            result = agent(f"Please solve this logic grid puzzle: {puzzle_str}")
            print("\nAgent result:")
            print(result)
            
            # Get structured output
            result_structured = structured_output_agent.structured_output(
                LogicGridResult,
                f"Format this logic grid solution: {result}"
            )
            
            print("\nStructured result:")
            print(result_structured.model_dump_json(indent=4))
            
        else:
            print("No puzzles found in dataset")
            
    except Exception as e:
        print(f"Error: {e}")
        
        # Test with a simple example
        example_puzzle = {
            "problem": "Three friends have different pets and live in different colored houses.",
            "clues": [
                "Alice lives in the red house",
                "The person with the cat lives in the blue house", 
                "Bob has a dog"
            ]
        }
        
        puzzle_str = str(example_puzzle)
        result = agent(f"Please solve this logic grid puzzle: {puzzle_str}")
        print("Test result with example puzzle:")
        print(result)