from typing import Any
from customAgents.tool_routers import BaseRouter


class InterruptRouter(BaseRouter):
    def __init__(self, interrupt_condition: Any, exec_after: float = 0):
        super().__init__(exec_after)

        self.interrupt_condition = interrupt_condition


    def exec_router(self, check_on):

        if check_on == self.interrupt_condition:
            return 0