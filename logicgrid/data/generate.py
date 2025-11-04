import json
import random
import csv  # Importado para guardar en CSV
from constraint import Problem, AllDifferentConstraint
from typing import List, Dict, Any, Optional, Tuple

# --- 1. CONFIGURACIÓN GLOBAL ---

N_PUZZLES_TO_GENERATE = 5
ALL_PUZZLES_GENERATED = []

# --- 2. MOLDES DE PUZZLES (Diversos) ---

PUZZLE_TEMPLATES = [
    {
        "id_prefix": "mascotas_3x3",
        "base_category": "Persona",
        "categories": {
            "Persona": ["Ana", "Beto", "Clara"],
            "Mascota": ["Gato", "Perro", "Pez"],
            "Ciudad": ["Lima", "Bogotá", "Quito"]
        }
    },
    {
        "id_prefix": "aventura_3x3",
        "base_category": "Héroe",
        "categories": {
            "Héroe": ["Ariana", "Balthazar", "Caelia"],
            "Arma": ["Espada", "Arco", "Báculo"],
            "Lugar": ["Bosque", "Castillo", "Caverna"]
        }
    },
    {
        "id_prefix": "trabajos_4x3", # 4 items, 3 categorías
        "base_category": "Nombre",
        "categories": {
            "Nombre": ["David", "Elena", "Fran", "Gloria"],
            "Trabajo": ["Doctor", "Chef", "Piloto", "Actor"],
            "Destino": ["París", "Tokio", "Sydney", "Cairo"]
        }
    },
    {
        "id_prefix": "cocina_4x3", # 4 items, 3 categorías
        "base_category": "Chef",
        "categories": {
            "Chef": ["Marco", "Lucía", "Javier", "Sofía"],
            "Plato": ["Pasta", "Curry", "Tacos", "Estofado"],
            "Restaurante": ["Sol", "Luna", "Mar", "Tierra"]
        }
    },
    {
        "id_prefix": "espacio_4x4", # 4 items, 4 categorías
        "base_category": "Capitán",
        "categories": {
            "Capitán": ["Zane", "Kira", "Rax", "Vex"],
            "Nave": ["Nova", "Orion", "Hyperion", "Sirius"],
            "Planeta": ["Xylos", "Glebar", "Rylon", "Phaedra"],
            "Misión": ["Explorar", "Diplomacia", "Carga", "Defensa"]
        }
    },
]

# --- 3. LÓGICA DE GENERACIÓN (Sin cambios) ---

def create_ground_truth(categories: Dict[str, List[str]], base_category: str) -> Dict[str, Dict[str, str]]:
    """
    Genera una solución (verdad fundamental) aleatoria y válida
    para un molde de categorías dado.
    """
    base_items = categories[base_category]
    other_categories = {k: v for k, v in categories.items() if k != base_category}
    
    solution = {item: {} for item in base_items}
    
    for cat_name, cat_items in other_categories.items():
        shuffled_items = random.sample(cat_items, k=len(base_items))
        
        for i, base_item in enumerate(base_items):
            solution[base_item][cat_name] = shuffled_items[i]
            
    return solution

def generate_all_possible_clues(ground_truth: Dict, categories: Dict, base_category: str) -> List[Dict]:
    """
    Genera un banco masivo de todas las pistas verdaderas
    (positivas, negativas y de enlace) basadas en la solución.
    """
    all_clues = []
    base_items = list(categories[base_category])
    
    for base_item in base_items:
        solution_for_item = ground_truth[base_item]
        
        # Pistas Positivas y Negativas
        for cat_name, solved_item in solution_for_item.items():
            all_clues.append({"type": "positive", "items": [base_item, solved_item]})
            for other_item in categories[cat_name]:
                if other_item != solved_item:
                    all_clues.append({"type": "negative", "items": [base_item, other_item]})
    
        # Pistas de Enlace (Link)
        solved_items_list = list(solution_for_item.values())
        for i in range(len(solved_items_list)):
            for j in range(i + 1, len(solved_items_list)):
                all_clues.append({"type": "link", "items": [solved_items_list[i], solved_items_list[j]]})

    unique_clues_json = {json.dumps(c, sort_keys=True) for c in all_clues}
    return [json.loads(c) for c in unique_clues_json]
    
def verify_solution(categories: Dict, base_category: str, structured_clues: List) -> List[Dict]:
    """
    Usa el Solucionador de Restricciones (CSP) para determinar
    cuántas soluciones existen para un conjunto de pistas.
    """
    problem = Problem()
    base_items = categories[base_category]
    other_category_names = [k for k in categories if k != base_category]
    
    variables = {}
    for base_item in base_items:
        variables[base_item] = {}
        for cat_name in other_category_names:
            var_name = f"{base_item}_{cat_name}"
            problem.addVariable(var_name, categories[cat_name])
            variables[base_item][cat_name] = var_name

    for cat_name in other_category_names:
        vars_for_cat = [variables[bi][cat_name] for bi in base_items]
        problem.addConstraint(AllDifferentConstraint(), vars_for_cat)

    # Añadir pistas como restricciones
    for clue in structured_clues:
        items = clue["items"]
        if clue["type"] == "positive":
            base_item, other = find_base_and_other_item(items, categories, base_category)
            if base_item and other:
                cat_name = get_category_name(other, categories)
                problem.addConstraint(lambda v, i=other: v == i, [variables[base_item][cat_name]])

        elif clue["type"] == "negative":
            base_item, other = find_base_and_other_item(items, categories, base_category)
            if base_item and other:
                cat_name = get_category_name(other, categories)
                problem.addConstraint(lambda v, i=other: v != i, [variables[base_item][cat_name]])

        elif clue["type"] == "link":
            item1, item2 = items
            cat1_name = get_category_name(item1, categories)
            cat2_name = get_category_name(item2, categories)
            if not cat1_name or not cat2_name or cat1_name == base_category or cat2_name == base_category:
                continue
            for base_item in base_items:
                var1, var2 = variables[base_item][cat1_name], variables[base_item][cat2_name]
                problem.addConstraint(
                    lambda v1, v2, i1=item1, i2=item2: (v1 != i1) or (v2 == i2), (var1, var2)
                )
                problem.addConstraint(
                    lambda v1, v2, i1=item1, i2=item2: (v2 != i2) or (v1 == i1), (var1, var2)
                )

    return problem.getSolutions()

def translate_clue_to_natural_language(clue: Dict, categories: Dict, base_category: str) -> str:
    """
    Convierte una pista estructurada en una frase simple
    en lenguaje natural, de forma genérica.
    """
    items = clue["items"]
    base_item, other_item = find_base_and_other_item(items, categories, base_category)
    
    if base_item:
        if clue["type"] == "positive":
            return f"{base_item} is directly associated with {other_item}."
        elif clue["type"] == "negative":
            return f"{base_item} is NOT associated with {other_item}."
    
    if clue["type"] == "link":
        item1, item2 = items
        return f"The item '{item1}' is linked to the same {base_category} as the item '{item2}'."
    
    return f"Clue: {clue['type']} - {', '.join(items)}"

# --- 4. FUNCIONES AUXILIARES (Sin cambios) ---

def get_category_name(item: str, categories: Dict) -> Optional[str]:
    for cat_name, items_list in categories.items():
        if item in items_list:
            return cat_name
    return None

def find_base_and_other_item(items: List[str], categories: Dict, base_category_name: str) -> Tuple[Optional[str], Optional[str]]:
    base_item, other_item = None, None
    for item in items:
        if item in categories[base_category_name]: base_item = item
        else: other_item = item
    return base_item, other_item

def format_puzzle_for_llm(puzzle_id: str, categories: Dict, natural_language_clues: List[str]) -> str:
    """
    Genera la representación de texto plano/markdown para el LLM.
    """
    output = f"## 🧩 New Logic Grid Puzzle (ID: {puzzle_id})\n\n"
    output += "Your task is to find the correct correspondence...\n\n"
    output += "### Categories\n"
    for cat_name, items_list in categories.items():
        output += f"* **{cat_name}:** {', '.join(items_list)}\n"
    output += "\n### Clues\n"
    for i, clue in enumerate(natural_language_clues, 1):
        output += f"{i}. {clue}\n"
    return output

# --- 5. ORQUESTADOR DE GENERACIÓN (Sin cambios) ---

def generate_puzzle_from_template(template: Dict, puzzle_index: int) -> Optional[Dict]:
    """
    Orquesta todo el proceso: Verdad -> Pistas -> Selección -> Verificación.
    """
    print(f"  Generando puzzle {puzzle_index} (molde: {template['id_prefix']})...")
    
    categories = template["categories"]
    base_category = template["base_category"]
    
    # 1. Generar Solución
    ground_truth = create_ground_truth(categories, base_category)
    
    # 2. Generar Banco de Pistas
    all_possible_clues = generate_all_possible_clues(ground_truth, categories, base_category)
    random.shuffle(all_possible_clues)
    
    # 3. Seleccionar Pistas (Método "Build-up")
    essential_clues = []
    
    initial_solutions = verify_solution(categories, base_category, [])
    if not initial_solutions:
        print("  Error: El molde es inherentemente contradictorio.")
        return None
        
    current_solution_count = len(initial_solutions)
    
    max_attempts = len(all_possible_clues) * 2
    attempts = 0
    clue_pool = all_possible_clues.copy()
    
    while current_solution_count > 1 and attempts < max_attempts:
        if not clue_pool: break
        attempts += 1
        
        clue = clue_pool.pop(random.randint(0, len(clue_pool)-1))
        potential_clues = essential_clues + [clue]
        new_solutions = verify_solution(categories, base_category, potential_clues)
        new_solution_count = len(new_solutions)
        
        if new_solution_count < current_solution_count and new_solution_count > 0:
            essential_clues.append(clue)
            current_solution_count = new_solution_count
            
    # 4. Verificación Final
    if current_solution_count != 1:
        print(f"  Fallo en la generación: No se pudo alcanzar una solución única (quedaron {current_solution_count}). Reintentando...")
        return None

    # 5. Traducir y Formatear
    natural_language_clues = [
        translate_clue_to_natural_language(c, categories, base_category)
        for c in essential_clues
    ]
    puzzle_id = f"{template['id_prefix']}_{puzzle_index}"
    
    llm_prompt = format_puzzle_for_llm(puzzle_id, categories, natural_language_clues)
    
    final_puzzle = {
        "puzzle_id": puzzle_id,
        "llm_prompt": llm_prompt,
        "ground_truth_solution": ground_truth,
        "structured_clues_used": essential_clues,
        "clue_count": len(essential_clues)
    }
    
    print(f"  ¡Éxito! Puzzle {puzzle_id} generado con {len(essential_clues)} pistas.")
    return final_puzzle


# --- 6. EJECUCIÓN PRINCIPAL ---

if __name__ == "__main__":
    print(f"Iniciando la generación de {N_PUZZLES_TO_GENERATE} puzzles...")
    
    puzzles_generated_count = 0
    
    while puzzles_generated_count < N_PUZZLES_TO_GENERATE:
        template = random.choice(PUZZLE_TEMPLATES)
        new_puzzle = generate_puzzle_from_template(template, puzzles_generated_count + 1)
        
        if new_puzzle:
            ALL_PUZZLES_GENERATED.append(new_puzzle)
            puzzles_generated_count += 1
            print("---")

    print("=====================================================")
    print(f"Generación completada. Total de puzzles en 'ALL_PUZZLES_GENERATED': {len(ALL_PUZZLES_GENERATED)}")
    print("=====================================================")

    # --- INICIO: BLOQUE PARA GUARDAR EN CSV (con separador '$') ---
    
    if ALL_PUZZLES_GENERATED:
        csv_filename = "generated_logic_puzzles.csv"
        
        fieldnames = [
            "puzzle_id",
            "clue_count",
            "llm_prompt",
            "ground_truth_solution_json",
            "structured_clues_json"
        ]

        print(f"\nGuardando {len(ALL_PUZZLES_GENERATED)} puzzles en {csv_filename} (separador: '$')...")
        
        try:
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as f:
                # --- ¡CAMBIO AQUÍ! ---
                # Añadido delimiter='$'
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='$')
                
                writer.writeheader()
                
                for puzzle in ALL_PUZZLES_GENERATED:
                    solution_json = json.dumps(puzzle["ground_truth_solution"])
                    clues_json = json.dumps(puzzle["structured_clues_used"])
                    
                    row_data = {
                        "puzzle_id": puzzle["puzzle_id"],
                        "clue_count": puzzle["clue_count"],
                        "llm_prompt": puzzle["llm_prompt"],
                        "ground_truth_solution_json": solution_json,
                        "structured_clues_json": clues_json
                    }
                    writer.writerow(row_data)
            
            print(f"¡Éxito! Archivo '{csv_filename}' guardado.")

        except Exception as e:
            print(f"Error al guardar el CSV: {e}")

    # --- FIN: BLOQUE CSV ---

    if ALL_PUZZLES_GENERATED:
        print("\nEjemplo de un puzzle generado (formato LLM):")
        print(random.choice(ALL_PUZZLES_GENERATED)["llm_prompt"])