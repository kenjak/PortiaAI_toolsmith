import logging
from dotenv import load_dotenv
import os
from portia import Portia
from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from portia.config import Config, LLMModel
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from openai import OpenAI
import textwrap
import ast

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Example calculator tool to use as a template
EXAMPLE_TOOL = '''
from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field

class CalculatorParams(BaseModel):
    """Parameters for the calculator tool."""
    expression: str = Field(..., description="Math expression to evaluate")

class Calculator(Tool[float]):
    """A simple calculator tool that evaluates mathematical expressions."""
    
    id: str = "calculator"
    name: str = "Calculator"
    description: str = "Evaluates mathematical expressions"
    args_schema: type[CalculatorParams] = CalculatorParams
    output_schema: tuple[str, str] = ("float", "Result of calculation")

    def run(self, ctx: ToolRunContext, expression: str) -> float:
        """Evaluate the mathematical expression."""
        try:
            # Basic security: only allow simple math operations
            allowed = set("0123456789+-*/(). ")
            if not all(c in allowed for c in expression):
                raise ToolHardError("Invalid characters in expression")
            
            result = eval(expression)
            if not isinstance(result, (int, float)):
                raise ToolHardError("Result must be a number")
                
            return float(result)
        except Exception as e:
            raise ToolHardError(f"Failed to evaluate expression: {str(e)}")
'''

class ToolGenerationParams(BaseModel):
    """Parameters for generating a new tool."""
    tool_name: str = Field(..., description="Name of the tool to create")
    task_description: str = Field(..., description="Detailed description of what the tool should do")
    input_params: List[str] = Field(default=[], description="List of input parameters the tool needs")
    output_type: str = Field(default="str", description="Expected return type of the tool")

class DynamicToolGenerator(Tool[str]):
    """Creates tools dynamically using Portia's planning system."""
    
    id: str = "create_tool"
    name: str = "Create Tool"
    description: str = "Creates a new Portia tool based on a task description"
    args_schema: type[ToolGenerationParams] = ToolGenerationParams
    output_schema: tuple[str, str] = ("str", "Result of tool creation")

    def run(self, ctx: ToolRunContext, tool_name: str, task_description: str, input_params: List[str], output_type: str) -> str:
        """Create a tool with the given parameters."""
        try:
            # Create a sub-portia instance to generate the tool code
            sub_config = Config.from_default(
                llm_provider="openai",
                llm_model_name=LLMModel.GPT_3_5_TURBO
            )
            sub_portia = Portia(config=sub_config)

            # Ask LLM to generate the tool's run method
            tool_query = f"""Write a simple Python function that {task_description}.
The function should:
1. Take parameters: {', '.join(input_params)}
2. Return a {output_type}
3. Be simple and focused

Example format:
```python
# Your code here
return "your result"
```

Return ONLY the function body."""

            result = sub_portia.run(tool_query)
            if not result.state == "COMPLETE" or not result.outputs.final_output:
                # Use default implementation if LLM fails
                generated_code = "# Default implementation\n"
                generated_code += f"return f\"Generated response for {', '.join(input_params)}\""
            else:
                # Extract the generated code
                generated_code = result.outputs.final_output.value.strip()
                if "```" in generated_code:
                    # Extract code from markdown code block if present
                    start = generated_code.find("```") + 3
                    end = generated_code.rfind("```")
                    if "python" in generated_code[start:start+10]:
                        start = generated_code.find("\n", start) + 1
                    generated_code = generated_code[start:end].strip()

            # Create the tool code with the generated functionality
            tool_code = f"""from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field

class {tool_name}Params(BaseModel):
    \"\"\"Parameters for the {tool_name} tool.\"\"\"
{chr(10).join(f'    {param}: str = Field(..., description="Parameter {param}")' for param in input_params)}

class {tool_name}(Tool[{output_type}]):
    \"\"\"A tool that {task_description}\"\"\"
    
    id: str = "{tool_name.lower()}"
    name: str = "{tool_name}"
    description: str = "{task_description}"
    args_schema: type[{tool_name}Params] = {tool_name}Params
    output_schema: tuple[str, str] = ("{output_type}", "Result of the operation")

    def run(self, ctx: ToolRunContext, {', '.join(f'{p}: str' for p in input_params)}) -> {output_type}:
        \"\"\"Execute the tool's functionality.\"\"\"
        {generated_code}
"""

            # Save the tool to a Python file
            tool_file = f"{tool_name.lower()}_tool.py"
            with open(tool_file, 'w') as f:
                f.write(tool_code)
            
            return f"Successfully created {tool_file}"
        except Exception as e:
            raise ToolHardError(f"Failed to create tool: {str(e)}")

class CodeComplexityAnalyzer:
    """A tool that analyzes code complexity."""

    def __init__(self):
        self.name = "CodeComplexityAnalyzer"
        self.description = "Analyzes a given Python code snippet for complexity metrics."

    def run(self, code: str) -> dict:
        """Analyze the provided code and return complexity metrics."""
        metrics = {
            "lines_of_code": self.count_lines_of_code(code),
            "cyclomatic_complexity": self.calculate_cyclomatic_complexity(code),
            "number_of_functions": self.count_functions(code),
            "comment_density": self.calculate_comment_density(code)
        }
        return metrics

    def count_lines_of_code(self, code: str) -> int:
        """Count the number of lines in the code."""
        return len(code.splitlines())

    def calculate_cyclomatic_complexity(self, code: str) -> int:
        """Calculate cyclomatic complexity using AST."""
        tree = ast.parse(code)
        complexity = 1  # Start with 1 for the method itself
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With)):
                complexity += 1
        return complexity

    def count_functions(self, code: str) -> int:
        """Count the number of function definitions in the code."""
        return code.count("def ")

    def calculate_comment_density(self, code: str) -> float:
        """Calculate the density of comments in the code."""
        lines = code.splitlines()
        comment_lines = sum(1 for line in lines if line.strip().startswith("#"))
        return comment_lines / len(lines) if lines else 0.0

# Initialize Portia with tool generator
config = Config.from_default(
    llm_provider="openai",
    llm_model_name=LLMModel.GPT_3_5_TURBO
)

portia = Portia(
    config=config,
    tools=[DynamicToolGenerator()]
)

def generate_greeting_logic() -> str:
    """Generate just the greeting logic using OpenAI."""
    try:
        prompt = """Write a simple Python if-else block that creates greetings based on time of day.
It should:
1. Use time_of_day and name as variables
2. Return a greeting string
3. Handle morning, afternoon, evening
4. Have a default case
5. Use f-strings for the output
6. Use 8 spaces for indentation

Example format:
if time_of_day.lower() == "morning":
        return f"Good morning, {name}!"

Return ONLY the if-else block."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Python code generator. Generate only the requested code, no explanations."},
                {"role": "user", "content": prompt}
            ]
        )
        
        generated_code = response.choices[0].message.content.strip()
        
        # Extract code from markdown if present
        if "```" in generated_code:
            start = generated_code.find("```") + 3
            end = generated_code.rfind("```")
            if "python" in generated_code[start:start+10]:
                start = generated_code.find("\n", start) + 1
            generated_code = generated_code[start:end].strip()
        
        # Fix indentation
        lines = generated_code.split('\n')
        fixed_lines = []
        for line in lines:
            if line.strip():  # If line is not empty
                if line.strip().startswith(('if', 'elif', 'else')):
                    fixed_lines.append(line.strip())  # No indent for control statements
                else:
                    fixed_lines.append('        ' + line.strip())  # 8 spaces for code blocks
        
        fixed_code = '\n'.join(fixed_lines)
        
        print("Generated greeting logic:")
        print(fixed_code)
        print("\nEnd of generated code")
        return fixed_code
            
    except Exception as e:
        print(f"Failed to generate greeting logic: {str(e)}")
        return None

def generate_tool_code(tool_name: str, task_description: str, input_params: List[str], output_type: str) -> str:
    """Generate tool code using OpenAI."""
    try:
        # Create a formatted string for the input parameters
        params_string = ', '.join(f'{param}: str' for param in input_params)

        # Prompt to generate the tool logic
        prompt = f"""Create a complete Python class that implements a tool named {tool_name}.
The class should:
1. Have an __init__ method that sets name and description.
2. Have a run method that takes parameters: {params_string}.
3. Return type should be {output_type}.
4. Implement the functionality described in: {task_description}.

Example of the exact format to follow:
```python
class ExampleTool:
    def __init__(self):
        self.name = "ExampleTool"
        self.description = "An example tool."

    def run(self, {params_string}) -> str:
        return f"Processed {', '.join(input_params)}"
```

Return ONLY the complete class code exactly as shown in the example, with proper indentation."""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a Python code generator. Generate only the requested code, no explanations."},
                {"role": "user", "content": prompt}
            ]
        )

        generated_code = response.choices[0].message.content.strip()

        # Extract code from markdown if present
        if "```