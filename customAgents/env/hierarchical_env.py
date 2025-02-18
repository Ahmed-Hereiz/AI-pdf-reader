import warnings
from typing import List, Union
from customAgents.env import SequentialEnv
from customAgents.tool_routers import BaseRouter
from customAgents.runtime import BaseRuntime


class HierarchialEnv(SequentialEnv):
    def __init__(self, env_items: Union[List[BaseRuntime], List[BaseRouter], List]):
        
        self.env_items = env_items

        super().__init__(env_items=self.env_items)

    def run(self, initial_input: str=""):

        current_input = initial_input

        for item in self.env_items:
            if type(item) is list:
                current_input = self.exec_inside_list(items=item,initial_input=current_input)
            elif isinstance(item, BaseRuntime):
                item.prompt.prompt += current_input
                current_input = item.loop()
            elif isinstance(item, BaseRouter):
                current_input = item.exec_router(current_input)

        return current_input


    def exec_inside_list(self, items: list, initial_input: str=""):

        agent_order = 0
        full_agents_response = ""

        for item in items:
            if isinstance(item, BaseRuntime):
                item.prompt.prompt += initial_input
                agent_output = item.loop()
                agent_order += 1
            else:
                warnings.warn(f"Warning!! you initialize in {items} a non BaseRuntime (agent) type element, skipping this item {item}")

            full_agents_response += f"response of Agent_{agent_order} is :\n\n {agent_output}\n\n"

        return "Given the previous question is revised by many AI agents and this is their responses :\n\n" + full_agents_response