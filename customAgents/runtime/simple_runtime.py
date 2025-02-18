from customAgents.runtime import BaseRuntime
from customAgents.agent_llm import BaseLLM
from customAgents.agent_prompt import BasePrompt


class SimpleRuntime(BaseRuntime):
    def __init__(self, llm: BaseLLM, prompt: BasePrompt):
        """Uses default BaseRuntime step and loop methods"""
        super().__init__(llm=llm, prompt=prompt, toolkit=[])


