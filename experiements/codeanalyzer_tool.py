from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from portia.config import Config, LLMModel
from portia import Portia
from pydantic import BaseModel, Field

class CodeAnalyzerParams(BaseModel):
    """Parameters for the CodeAnalyzer tool."""
    code: str = Field(..., description="Code to analyze")

class CodeAnalyzer(Tool[dict]):
    """A tool that Analyze code complexity and structure, examining factors like conditionals, loops, nesting depth, function length, and variable usage. Return detailed analysis including complexity score, issues found, and suggestions for improvement."""
    
    id: str = "codeanalyzer"
    name: str = "CodeAnalyzer"
    description: str = "Analyze code complexity and structure, examining factors like conditionals, loops, nesting depth, function length, and variable usage. Return detailed analysis including complexity score, issues found, and suggestions for improvement."
    args_schema: type[CodeAnalyzerParams] = CodeAnalyzerParams
    output_schema: tuple[str, str] = ("dict", "Result of the operation")

    def run(self, ctx: ToolRunContext, code: str = None) -> dict:
        """Execute the tool's functionality."""
        try:
            # If code is not provided, try to extract it from the context
            if code is None:
                # Try to find code in the query
                query = ctx.query
                if "```" in query:
                    # Extract code between triple backticks
                    start = query.find("```") + 3
                    end = query.rfind("```")
                    if start < end:
                        code = query[start:end].strip()
                        if code.startswith("python\n"):
                            code = code[7:]
                else:
                    # Try to find code after "code:" or similar markers
                    markers = ["code:", "code =", "code="]
                    for marker in markers:
                        if marker in query:
                            start = query.find(marker) + len(marker)
                            code = query[start:].strip()
                            break

            if not code:
                raise ToolHardError("No code provided for analysis")

            # Create a sub-portia instance to handle the task
            sub_config = Config.from_default(
                llm_provider="openai",
                llm_model_name=LLMModel.GPT_3_5_TURBO
            )
            sub_portia = Portia(config=sub_config)

            # Use Portia to analyze the input
            task_query = f"""
            Task: Analyze code complexity and structure, examining factors like conditionals, loops, nesting depth, function length, and variable usage. Return detailed analysis including complexity score, issues found, and suggestions for improvement.
            Code to analyze:
            {code}

            Analyze the code and return a detailed dictionary containing:
            1. Complexity score (1-10)
            2. Issues found
            3. Suggestions for improvement
            4. Analysis of conditionals, loops, nesting depth, function length, and variable usage
            """

            result = sub_portia.run(task_query)
            if result.state == "COMPLETE" and result.outputs.final_output:
                if isinstance(result.outputs.final_output.value, str):
                    import json
                    try:
                        return json.loads(result.outputs.final_output.value)
                    except:
                        return {
                            "analysis": result.outputs.final_output.value,
                            "format": "text",
                            "status": "completed"
                        }
                return result.outputs.final_output.value
            else:
                raise ToolHardError("Failed to process the request")

        except Exception as e:
            raise ToolHardError(f"Operation failed: {str(e)}")
