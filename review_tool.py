from typing import List
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (like your API key)
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def strip_code_noise(code: str) -> str:
    """
    Cleans code output from GPT-style tools by removing:
    - Markdown code fences (```python and ```)
    - Common non-code lines like "Here's a Python function..."
    - Blank lines around the code
    """
    code = code.replace("```python", "").replace("```", "").strip()
    lines = code.splitlines()
    cleaned = "\n".join(
        line for line in lines
        if not line.strip().lower().startswith("here is")
        and not line.strip().lower().startswith("this function")
        and not line.strip().lower().startswith("example usage")
    )
    return cleaned.strip()

def review_tool(code: str) -> str:
    """
    Uses GPT-4 to review a Python tool function and provide structured feedback
    on design, error handling, clarity, testability, and suggestions for improvement.

    Args:
        code (str): The full Python code of the tool function.

    Returns:
        str: A structured code review summary.
    """
    prompt = f"""
You are a professional Python code reviewer.

Please review the following tool function and give detailed feedback on:
- Design and architecture
- Input validation and error handling
- Code clarity and maintainability
- Security or ethical considerations (if applicable)
- Opportunities for improvement
- Suggestions for testing

Only provide the review, not the code.

Here is the tool code:
```python
{code}
```
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

def tool_prompt(original_code=None, feedback=None):
    if feedback and original_code:
        return f"""
You previously created a Python function based on a user request.

Here is the original function code:
```python
{original_code}
```

Here is the feedback from a code reviewer:
{feedback}

Please revise and improve the function accordingly. Keep the same structure, inputs, and purpose. Do not remove any existing logic unless it's incorrect. Only make improvements based on the review.
Return only the improved Python function code. Do not include any explanation, description, or markdown syntax.
"""
    elif feedback:
        return f"""
You previously created a Python function based on a user request.

Here is the feedback from a code reviewer:
{feedback}

Please revise and improve the function accordingly. Keep the same structure and inputs, but enhance the implementation based on the review.
Return only the updated Python function code. Do not include any explanation, description, or markdown syntax.
"""

        return f"""
Write a complete Python function called `{tool_name}`.

It should:
- {tool_purpose}
- Use these inputs: {tool_inputs}
- Return: {tool_output}

Use full Python syntax with type hints and a detailed docstring.
Wrap the function with `@tool` from the `portia` package.
Use `openai.ChatCompletion.create(...)` if calling an LLM.
Return only the Python function code.
Do not include any explanation or markdown code fences.
"""
