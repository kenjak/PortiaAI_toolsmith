```python
import openai
from typing import List, Dict, Optional

def generate_recipe_llm(api_key: str, ingredients: List[str], cuisine: Optional[str] = None) -> Dict[str, List[str]]:
    """
    Generates a recipe using GPT-4 via the OpenAI API based on the provided ingredients and optional cuisine style.

    Parameters:
    - api_key (str): The API key for accessing the OpenAI API.
    - ingredients (List[str]): A list of ingredients to be used in the recipe.
    - cuisine (Optional[str]): An optional string specifying the desired cuisine style.

    Returns:
    - Dict[str, List[str]]: A dictionary containing the recipe with the following keys:
        - 'title': A list containing the title of the recipe as a single string.
        - 'ingredients': A list of strings, each representing an ingredient in the recipe.
        - 'instructions': A list of strings, each representing a step in the recipe instructions.
    """
    openai.api_key = api_key

    prompt = f"Create a recipe using the following ingredients: {', '.join(ingredients)}."
    if cuisine:
        prompt += f" The recipe should be in the style of {cuisine} cuisine."

    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=500,
        n=1,
        stop=None,
        temperature=0.7
    )

    recipe_text = response.choices[0].text.strip()
    lines = recipe_text.split('\n')
    
    title = lines[0]
    ingredients_list = []
    instructions_list = []
    is_ingredients_section = True

    for line in lines[1:]:
        if line.strip() == "":
            continue
        if is_ingredients_section:
            if line.lower().startswith("instructions"):
                is_ingredients_section = False
                continue
            ingredients_list.append(line.strip())
        else:
            instructions_list.append(line.strip())

    return {
        "title": [title],
        "ingredients": ingredients_list,
        "instructions": instructions_list
    }
```