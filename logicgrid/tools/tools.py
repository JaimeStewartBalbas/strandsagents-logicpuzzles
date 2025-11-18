from .solvers import solve_logic_grid_puzzle_tool
from strands import tool


@tool
def solve_logic_grid_tool(entities: list[str], attributes: dict[str, list[str]], clues: list[dict]) -> dict:
    """
    Solves a logic grid puzzle using constraint satisfaction.
    
    Args:
        entities: List of entities (people)
        attributes: Dictionary with attributes and their possible values
        clues: List of clues with types: eq, neq, cross_eq, cross_neq
    
    Returns:
        Puzzle solution as dictionary {entity: {attribute: value}}
    """
    # print("="*10)
    # print("USING  SOLVE LOGIC GRID TOOL")
    # print("="*10)

    # print("Entities: ", entities)
    # print("Attributes: ", attributes)
    # print("Clues: ", clues)

    return "The solution of the logic grid puzzle is : " + str(solve_logic_grid_puzzle_tool(entities, attributes, clues))
