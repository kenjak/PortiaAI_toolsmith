from portia.tool import Tool, ToolRunContext
from portia.errors import ToolHardError
from pydantic import BaseModel, Field

class EchoParams(BaseModel):
    """Parameters for the Echo tool."""
    message: str = Field(..., description="Message to echo back")

class Echo(Tool[str]):
    """A tool that Create a tool that echoes back its input."""
    
    id: str = "echo"
    name: str = "Echo"
    description: str = "Create a tool that echoes back its input."
    args_schema: type[EchoParams] = EchoParams
    output_schema: tuple[str, str] = ("str", "Echoed message")

    def run(self, ctx: ToolRunContext, message: str) -> str:
        """Simply return the input message."""
        return f"Echo: {message}"
