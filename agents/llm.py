from strands import Agent
from pydantic import BaseModel, Field
from strands.models.ollama import OllamaModel
from data.load import format_sudoku

# Define Pydantic model for structured output
class SudokuResult(BaseModel):
    sudoku: str = Field(description="Original Sudoku puzzle as an 81-digit string")
    solution: str = Field(description="Solved Sudoku as an 81-digit string")

# Create Ollama model instance
ollama_model = OllamaModel(
    host="http://localhost:11434",
    model_id="qwen3:14b"
)

# Strict system prompt: enforce JSON-only output
SYSTEM_PROMPT = """
You are a Sudoku-solving assistant.
You will receive a flattened 4x4 Sudoku puzzle as a string of 16 digits (0 represents empty cells) and spaces indicate different rows.
Solve the puzzle using your reasoning capabilities quickly.

IMPORTANT: Your response must be a JSON object **exactly** in this format and nothing else:

{
    "sudoku": "<the original 16-digit puzzle string>",
    "solution": "<the 16-digit solution string>"
}

Return **only the JSON object**.

Examples:
User input: Please solve this sudoku: 4032320003140000
Your output: {
    "sudoku": "4032320003140000",
    "solution": "4132324123141423"
}

User input: Can you solve this sudoku: 3001142320000002
Your output: {
    "sudoku": "3001142320000002",
    "solution": "3241142321344312"
}
User input:
"""

# Create the agent
agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT,
)

# Example Sudoku puzzle
puzzle = "0431 3000 0013 1300"
expected_solution ="2431312442131342"


SYSTEM_PROMPT_FORMATTER = """
You are a formatting assistant.
You must format the Sudoku solution provided by the input and return SudokuResult object.
"""

structured_output_agent = Agent(
    model=ollama_model,
    system_prompt=SYSTEM_PROMPT_FORMATTER,
    callback_handler=None,
)



# Run agent using structured_output to enforce JSON parsing
try:
    result_structured = agent(f"Can you solve this sudoku?: {puzzle}")
    
    
    
    result_structured = structured_output_agent.structured_output(
        SudokuResult,
        f"Format this sudoku solution: {result_structured}"
    )
    
    # Print the raw JSON object
    print("\nStructured JSON output:\n", result_structured.model_dump_json(indent=4))

    print("\nFormatted Sudoku Puzzle:\n")
    print(format_sudoku(result_structured.sudoku))
    
    # Optionally, print a formatted Sudoku for visualization
    print("\nFormatted Sudoku Solution:\n")
    print(format_sudoku(result_structured.solution))
    
    print("\nValidation Summary:")
    print("Is the input valid?", result_structured.sudoku == puzzle)
    print("Is the solution valid?", result_structured.solution == expected_solution)

except KeyboardInterrupt:
    print("\nExecution interrupted by user (Ctrl+C). Exiting immediately.")
except Exception as e:
    print("Error during agent execution:", e)
