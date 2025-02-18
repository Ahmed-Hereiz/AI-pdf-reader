from typing import List
from customAgents.env import BaseEnv
from customAgents.tool_routers import BaseRouter


class MultiRoutersEnv(BaseEnv):
    def __init__(self, routers: List[BaseRouter]):

        super().__init__(agents=None, routers=routers)

        self.routers = routers

    def run(self, initial_input):

        current_input = initial_input

        for router in self.routers:
            if isinstance(router, BaseRouter):
                current_input = router.exec_router(current_input)
            else:
                raise NotImplementedError("only implemented type in MultiRoutersEnv is Routers")
            
            return current_input
        
    def get_item(self, index: int):
        """
        Returns the item at the specified index.

        :param index: The index of the agent to retrieve.
        :return: The item at the specified index.
        :raises IndexError: If the index is out of range.
        """
        if index >= len(self.env_items):
            raise ValueError("index number is more than the len of the items list")

        return self.env_items[index]