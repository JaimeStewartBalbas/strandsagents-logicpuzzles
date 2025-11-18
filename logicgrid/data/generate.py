import json
import uuid
import random
from itertools import permutations
from pathlib import Path

# ───────────────────────────────
# Configuration
# ───────────────────────────────
NUM_PUZZLES = 100
MIN_ENTITIES = 3
MAX_ENTITIES = 4

NAME_POOL = [
    "Alice","Bob","Carol","David","Eva","Frank","Grace","Hugo","Irene","Jorge",
    "Marta","Nico","Olga","Pablo","Quinn","Sara","Vera"
]

ATTRIBUTE_POOLS = {
    "color": ["red","blue","green","yellow","purple"],
    "animal": ["cat","dog","fish","hamster","bird"],
    "drink": ["coffee","tea","juice","water","soda"],
    "city": ["Madrid","Rome","London","Paris","Berlin"],
    "sport": ["tennis","football","swimming","basketball","yoga"],
    "food": ["pizza","salad","sushi","pasta","tacos"]
}

# ───────────────────────────────
# Helper: generate natural text
# ───────────────────────────────
def generate_text(entities, attributes, clues_text):
    attr_desc = []
    for attr, values in attributes.items():
        attr_desc.append(f"{attr}: {', '.join(values)}")
    attr_text = "; ".join(attr_desc)

    narrative = f"There are {len(entities)} people: {', '.join(entities)}.\n"
    narrative += f"The attributes are: {attr_text}.\n"
    narrative += "Clues:\n"
    for c in clues_text:
        narrative += f"- {c}\n"
    narrative += "\nDetermine which attributes correspond to each person."
    return narrative

# ───────────────────────────────
# Helper: generate structured clues
# ───────────────────────────────
def generate_structured_clues(entities, attributes, solution):
    clues_text = []
    clues_structured = []
    used_facts = set()  # Avoid redundant clues

    # 1. One direct positive statement (only one to not give too much information)
    entity = random.choice(entities)
    attr = random.choice(list(attributes.keys()))
    value = solution[entity][attr]
    clues_text.append(f"{entity} has {value}.")
    clues_structured.append({"type":"eq","entity":entity,"attr":attr,"value":value})
    used_facts.add((entity, attr, value))

    # 2. Strategic negations
    neg_count = 0
    max_negations = len(entities) + 1
    while neg_count < max_negations:
        entity = random.choice(entities)
        attr = random.choice(list(attributes.keys()))
        choices = [v for v in attributes[attr] if v != solution[entity][attr]]
        if choices:
            val = random.choice(choices)
            if (entity, attr, val, "neq") not in used_facts:
                clues_text.append(f"{entity} doesn't have {val}.")
                clues_structured.append({"type":"neq","entity":entity,"attr":attr,"value":val})
                used_facts.add((entity, attr, val, "neq"))
                neg_count += 1

    # 3. More varied cross-comparisons
    cross_count = 0
    max_cross = len(attributes) if len(attributes) > 2 else 2
    
    while cross_count < max_cross:
        if len(attributes) < 2:
            break
            
        attr1, attr2 = random.sample(list(attributes.keys()), 2)
        
        # Choose values that are actually in the solution
        entity1 = random.choice(entities)
        val1 = solution[entity1][attr1]
        
        # For cross_eq: use same entity
        # For cross_neq: use different entity
        clue_type = random.choice(["cross_neq", "cross_eq"])
        
        if clue_type == "cross_eq":
            val2 = solution[entity1][attr2]  # Same entity
            cross_key = (attr1, val1, attr2, val2, "eq")
        else:
            # Find a different entity to create a valid negation
            other_entities = [e for e in entities if e != entity1]
            if other_entities:
                entity2 = random.choice(other_entities)
                val2 = solution[entity2][attr2]
                cross_key = (attr1, val1, attr2, val2, "neq")
            else:
                continue
        
        if cross_key not in used_facts:
            if clue_type == "cross_neq":
                clues_text.append(f"The person with {val1} {attr1} doesn't have {val2} {attr2}.")
                clues_structured.append({"type":"cross_neq","attr1":attr1,"value1":val1,"attr2":attr2,"value2":val2})
            else:
                clues_text.append(f"Whoever has {val1} {attr1} has {val2} {attr2}.")
                clues_structured.append({"type":"cross_eq","attr1":attr1,"value1":val1,"attr2":attr2,"value2":val2})
            
            used_facts.add(cross_key)
            cross_count += 1

    random.shuffle(clues_text)
    return clues_text, clues_structured

# ───────────────────────────────
# Generator
# ───────────────────────────────
from constraint import Problem, AllDifferentConstraint

def has_unique_solution(entities, attributes, clues):
    """
    Checks if the puzzle has exactly one solution using python-constraint.
    """
    problem = Problem()
    
    # Add variables for each entity-attribute
    for attr, values in attributes.items():
        for entity in entities:
            problem.addVariable(f"{entity}_{attr}", values)
    
    # Each attribute must have unique values among entities
    for attr in attributes:
        problem.addConstraint(AllDifferentConstraint(), [f"{e}_{attr}" for e in entities])
    
    # Apply clue constraints
    for clue in clues:
        if clue["type"] == "eq":
            e, a, v = clue["entity"], clue["attr"], clue["value"]
            problem.addConstraint(lambda x, val=v: x == val, [f"{e}_{a}"])
        elif clue["type"] == "neq":
            e, a, v = clue["entity"], clue["attr"], clue["value"]
            problem.addConstraint(lambda x, val=v: x != val, [f"{e}_{a}"])
        elif clue["type"] == "cross_eq":
            # Whoever has v1 in a1 also has v2 in a2
            a1, v1, a2, v2 = clue["attr1"], clue["value1"], clue["attr2"], clue["value2"]
            vars_a1 = [f"{e}_{a1}" for e in entities]
            vars_a2 = [f"{e}_{a2}" for e in entities]
            
            def cross_eq_constraint(*args):
                n = len(entities)
                vals_a1 = args[:n]
                vals_a2 = args[n:]
                # If any entity has v1 in a1, it must have v2 in a2
                for i in range(n):
                    if vals_a1[i] == v1 and vals_a2[i] != v2:
                        return False
                return True
            
            problem.addConstraint(cross_eq_constraint, vars_a1 + vars_a2)
        elif clue["type"] == "cross_neq":
            # Whoever has v1 in a1 does NOT have v2 in a2
            a1, v1, a2, v2 = clue["attr1"], clue["value1"], clue["attr2"], clue["value2"]
            vars_a1 = [f"{e}_{a1}" for e in entities]
            vars_a2 = [f"{e}_{a2}" for e in entities]
            
            def cross_neq_constraint(*args):
                n = len(entities)
                vals_a1 = args[:n]
                vals_a2 = args[n:]
                # No entity can have v1 in a1 AND v2 in a2
                for i in range(n):
                    if vals_a1[i] == v1 and vals_a2[i] == v2:
                        return False
                return True
            
            problem.addConstraint(cross_neq_constraint, vars_a1 + vars_a2)
    
    solutions = problem.getSolutions()
    return len(solutions) == 1

# ───────────────────────────────
# Modified generate_puzzle
# ───────────────────────────────
def generate_puzzle():
    max_attempts = 500  # Avoid infinite loops
    
    for attempt in range(max_attempts):
        n_entities = random.randint(MIN_ENTITIES, MAX_ENTITIES)
        entities = random.sample(NAME_POOL, n_entities)

        # Select 2-3 attributes
        num_attrs = random.choice([2, 3]) if len(ATTRIBUTE_POOLS) >= 3 else 2
        attribute_names = random.sample(list(ATTRIBUTE_POOLS.keys()), num_attrs)
        
        attributes = {attr: random.sample(ATTRIBUTE_POOLS[attr], n_entities) for attr in attribute_names}

        # Generate random solution (not sequential)
        solution = {}
        for attr in attribute_names:
            shuffled_values = attributes[attr].copy()
            random.shuffle(shuffled_values)
            for i, person in enumerate(entities):
                if person not in solution:
                    solution[person] = {}
                solution[person][attr] = shuffled_values[i]

        # Generate clues
        clues_text, clues_structured = generate_structured_clues(entities, attributes, solution)
        
        # Verify we have enough clues
        if len(clues_structured) < len(entities):
            continue

        # Validate uniqueness
        if has_unique_solution(entities, attributes, clues_structured):
            text_prompt = generate_text(entities, attributes, clues_text)
            return {
                "id": str(uuid.uuid4()),
                "text_prompt": text_prompt,
                "entities": entities,
                "attributes": attributes,
                "clues": clues_structured,
                "solution": solution
            }
    
    # If couldn't generate a valid puzzle, try with minimal configuration
    print(f"Warning: Could not generate unique puzzle in {max_attempts} attempts")
    return None

# ───────────────────────────────
# Main
# ───────────────────────────────
def generate_dataset(filename="logic_puzzles_auto.jsonl"):
    output = Path(filename)
    generated_count = 0
    
    with output.open("w", encoding="utf8") as f:
        for i in range(NUM_PUZZLES):
            puzzle = generate_puzzle()
            if puzzle is not None:
                f.write(json.dumps(puzzle, ensure_ascii=False) + "\n")
                generated_count += 1
            
            if (i + 1) % 10 == 0:
                print(f"Progress: {i + 1}/{NUM_PUZZLES} attempts, {generated_count} puzzles generated")

    print(f"Generated {generated_count} valid puzzles out of {NUM_PUZZLES} attempts → {output.absolute()}")
    if generated_count < NUM_PUZZLES:
        print(f"Note: Only generated {generated_count} valid puzzles out of {NUM_PUZZLES} requested")

if __name__ == "__main__":
    generate_dataset()