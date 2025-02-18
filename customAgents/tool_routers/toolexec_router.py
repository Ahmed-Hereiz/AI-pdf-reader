from customAgents.tool_routers import BaseRouter
from customAgents.agent_tools import BaseTool


class ToolExecRouter(BaseRouter):
    def __init__(self, tool: BaseTool, exec_after: float = 0):
        super().__init__(exec_after)

        self.tool = tool

    def exec_router(self, *params):

        return self.tool.execute_func(*params)



    