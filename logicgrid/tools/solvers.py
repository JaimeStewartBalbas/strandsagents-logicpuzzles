from constraint import Problem, AllDifferentConstraint

def solve_logic_grid_puzzle_tool(entities, attributes, clues):
    """
    Resuelve un logic grid puzzle usando python-constraint.
    
    Args:
        entities: list[str]  e.g. ["Raúl", "Irene", "Quinn", "Frank"]
        attributes: dict[attr_name -> list[values]] e.g. {"animal": [...], "ciudad": [...], ...}
        clues: list[dict] con tipo: eq, neq, cross_eq, cross_neq
    
    Returns:
        solution: dict {entity: {attr: value}}
    """
    problem = Problem()
    
    # Crear variables: cada entidad para cada atributo
    for attr, values in attributes.items():
        for entity in entities:
            problem.addVariable(f"{entity}_{attr}", values)
    
    # Todos los valores de cada atributo deben ser distintos
    for attr in attributes:
        problem.addConstraint(AllDifferentConstraint(), [f"{entity}_{attr}" for entity in entities])
    
    # Aplicar las pistas
    for clue in clues:
        if clue["type"] == "eq":
            entity = clue["entity"]
            attr = clue["attr"]
            value = clue["value"]
            problem.addConstraint(lambda v, val=value: v == val, [f"{entity}_{attr}"])
        
        elif clue["type"] == "neq":
            entity = clue["entity"]
            attr = clue["attr"]
            value = clue["value"]
            problem.addConstraint(lambda v, val=value: v != val, [f"{entity}_{attr}"])
        
        elif clue["type"] == "cross_eq":
            attr1, val1 = clue["attr1"], clue["value1"]
            attr2, val2 = clue["attr2"], clue["value2"]
            def cross_eq_func(*args):
                # args: [e1_attr1, e2_attr1,..., e1_attr2, e2_attr2,...]
                n = len(entities)
                vals_attr1 = args[:n]
                vals_attr2 = args[n:]
                for i in range(n):
                    if vals_attr1[i] == val1 and vals_attr2[i] != val2:
                        return False
                return True
            problem.addConstraint(cross_eq_func,
                [f"{e}_{attr1}" for e in entities] + [f"{e}_{attr2}" for e in entities])
        
        elif clue["type"] == "cross_neq":
            attr1, val1 = clue["attr1"], clue["value1"]
            attr2, val2 = clue["attr2"], clue["value2"]
            def cross_neq_func(*args):
                n = len(entities)
                vals_attr1 = args[:n]
                vals_attr2 = args[n:]
                for i in range(n):
                    if vals_attr1[i] == val1 and vals_attr2[i] == val2:
                        return False
                return True
            problem.addConstraint(cross_neq_func,
                [f"{e}_{attr1}" for e in entities] + [f"{e}_{attr2}" for e in entities])
    
    # Tomar la primera solución encontrada
    sol = problem.getSolution()
    if sol is None:
        return None
    
    # Reconstruir formato {entity: {attr: value}}
    solution = {entity:{} for entity in entities}
    for entity in entities:
        for attr in attributes:
            solution[entity][attr] = sol[f"{entity}_{attr}"]
    
    return solution



def check_solution(expected:dict, actual:dict):
    """
    Compara dos soluciones de un logic grid puzzle y muestra diferencias.

    Args:
        expected: dict {entity: {attr: value}}
        actual: dict {entity: {attr: value}}

    Returns:
        True si son exactamente iguales, False si hay alguna diferencia
    """
    equal = True

    # Comprobar entidades
    expected_entities = set(expected.keys())
    actual_entities = set(actual.keys())
    if expected_entities != actual_entities:
        print(f"Diferencia en entidades:\nExpected: {expected_entities}\nActual: {actual_entities}")
        equal = False

    # Comprobar atributos de cada entidad
    for entity in expected_entities & actual_entities:
        expected_attrs = set(expected[entity].keys())
        actual_attrs = set(actual[entity].keys())
        if expected_attrs != actual_attrs:
            print(f"Diferencia en atributos de {entity}:\nExpected: {expected_attrs}\nActual: {actual_attrs}")
            equal = False
        # Comprobar valores
        for attr in expected_attrs & actual_attrs:
            if expected[entity][attr] != actual[entity][attr]:
                print(f"Diferencia en {entity} -> {attr}: Expected={expected[entity][attr]}, Actual={actual[entity][attr]}")
                equal = False

    return equal



if __name__ == "__main__":
    puzzle = {"id": "7b3f0778-a3f9-4cbe-a982-cf65f41d07c3", "text_prompt": "Clues: - Whoever has hamster animal has Paris city.\n- Nico doesn't have dog.\n- Pablo has Madrid.\n- Whoever has Berlin city has dog animal.\n- Eva doesn't have fish.\n- Pablo doesn't have Berlin.\n- Nico doesn't have fish.\n\nDetermine which attributes correspond to each person.", "entities": ["Pablo", "Eva", "Nico"], "attributes": {"animal": ["fish", "hamster", "dog"], "city": ["Paris", "Madrid", "Berlin"]}, "clues": [{"type": "eq", "entity": "Pablo", "attr": "city", "value": "Madrid"}, {"type": "neq", "entity": "Nico", "attr": "animal", "value": "fish"}, {"type": "neq", "entity": "Eva", "attr": "animal", "value": "fish"}, {"type": "neq", "entity": "Pablo", "attr": "city", "value": "Berlin"}, {"type": "neq", "entity": "Nico", "attr": "animal", "value": "dog"}, {"type": "cross_eq", "attr1": "city", "value1": "Berlin", "attr2": "animal", "value2": "dog"}, {"type": "cross_eq", "attr1": "animal", "value1": "hamster", "attr2": "city", "value2": "Paris"}], "solution": {"Pablo": {"animal": "fish", "city": "Madrid"}, "Eva": {"animal": "dog", "city": "Berlin"}, "Nico": {"animal": "hamster", "city": "Paris"}}}

    solution = solve_logic_grid_puzzle_tool(puzzle["entities"], puzzle["attributes"],puzzle["clues"])

    print("Solution:")
    print((solution))
 

    print("Check:")
    print(check_solution(solution, puzzle["solution"]))