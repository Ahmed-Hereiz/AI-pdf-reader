from customAgents.ml_models import BaseModels
from customAgents.agent_tools import BaseTool


class ModelInferenceTool(BaseTool):
    def __init__(
            self,
            model: BaseModels,
            description: str = "Tool used to inference other machine learning models",
            tool_name: str = None,
    ):
        self.model = model
        super().__init__(description, tool_name)

    def execute_func(self, *args, **kwargs):

        result = self.model.inference(*args, **kwargs)

        if isinstance(result, str):
            return f"Text result: {result}", result
        elif isinstance(result, list): 
            return f"List result with {len(result)} items.", result
        elif isinstance(result, dict):  
            return f"Dictionary result: {result.keys()}", result
        else:
            return f"returned result type: {type(result)}", result
