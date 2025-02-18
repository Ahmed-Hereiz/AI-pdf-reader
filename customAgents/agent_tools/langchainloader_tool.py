from customAgents.agent_tools import BaseTool
from typing import Any

class LangchainToolLoader(BaseTool):
    def __init__(self, tool_name: str, description: str):
        super().__init__(tool_name, description)

    def execute_func(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError("Subclasses must implement execute_func method")
