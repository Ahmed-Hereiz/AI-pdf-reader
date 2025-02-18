from typing import List, Union
from customAgents.env import BaseEnv
from customAgents.tool_routers import BaseRouter
from customAgents.runtime import BaseRuntime


class SequentialEnv(BaseEnv):
    def __init__(self, env_items: Union[List[BaseRuntime],List[BaseRouter]]):
        if len(env_items) < 2:
            raise ValueError("SequentialEnv class needs at least 2 or more agents or routers to work")
        
        self.env_items = env_items

        super().__init__(agents=None, routers=None)

    def run(self, initial_input: str=""):

        current_input = initial_input

        for item in self.env_items:

            if isinstance(item, BaseRuntime):
                item.prompt.prompt += current_input
                current_input = item.loop()
            elif isinstance(item, BaseRouter):
                current_input = item.exec_router(current_input)

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