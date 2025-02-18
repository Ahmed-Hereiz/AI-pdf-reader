from customAgents.runtime import BaseRuntime
from customAgents.agent_llm import BaseLLM
from customAgents.agent_prompt import BasePrompt
from customAgents.agent_tools import ToolKit


class ChooseToolRuntime(BaseRuntime):
    def __init__(self, llm: BaseLLM, prompt: BasePrompt, toolkit: ToolKit):

        super().__init__(llm, prompt, toolkit)


    def step(self) -> str:
        return super().step()
    

    def loop(self, n_steps: int = 1) -> str:

        self.prompt.prompt = self.prompt.prompt.replace("{tools}",self.toolkit.tool_names)

        return super().loop(n_steps)