from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from tools.sudoku import solve_sudoku_tool, show_sudoku, validate_sudoku_solution
from sudoku.data.load import format_sudoku

# Pydantic model defining the expected JSON output
class SudokuResult(BaseModel):
    """Structured output for a solved Sudoku."""
    sudoku: str = Field(description="Original Sudoku puzzle as an 81-digit string")
    solution: str = Field(description="Solved Sudoku as an 81-digit string")


# Create an Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",  
    model_id="qwen3:8b"              
)

SYSTEM_PROMPT = """
You are a Sudoku-solving agent. You have access to tools that can help you solve and validate Sudoku puzzles.
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
      - If the solution is invalid, return a JSON with "solution": null.
   c. Do NOT attempt to solve, format, or validate the Sudoku yourself; rely only on the tools.
2. Return a JSON following the exact schema above.
"""

# Create an agent using the Ollama model and both tools
agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT,
   # callback_handler=None,
    tools=[solve_sudoku_tool, show_sudoku,validate_sudoku_solution]
)

# Example Sudoku
puzzle = "400053270020600803008904010145200006000048300000001090601300450000070900780000060"

# Use structured output to get a type-safe response
result = agent(f"Please solve this sudoku: {puzzle}")


SYSTEM_PROMPT_FORMATTER = """
You are a formatting assistant.
You must format the Sudoku solution provided by the input and return SudokuResult object.
"""

structured_output_agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT_FORMATTER,
    #callback_handler=None,
)

result_structured = structured_output_agent.structured_output(
    SudokuResult,
    f"Format this sudoku solution: {result}"
)

# # Print structured output
print(result_structured.model_dump_json(indent=4))

print("\nFormatted Sudoku Solution:\n")
print(format_sudoku(result_structured.solution))

expected_solution = "416853279529617843378924615145239786967548321832761594691382457254176938783495162"

print("\nExpected output:\n", format_sudoku(expected_solution))

print("\nValidation Summary:")
print("Is the input valid?", result_structured.sudoku == puzzle)
print("Is the solution valid?", result_structured.solution == expected_solution)

