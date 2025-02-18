from typing import Any
from customAgents.agent_llm import SimpleStreamLLM
from customAgents.agent_prompt import ReActPrompt
from customAgents.agent_tools import ToolKit, PythonRuntimeTool
from customAgents.runtime import ReActRuntime


class PythonCodingLLM(SimpleStreamLLM):
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, safety_settings: Any = None, max_output_tokens: int = None):
        super().__init__(api_key, model, temperature, safety_settings, max_output_tokens)


class PythonCodingPrompt(ReActPrompt):
    def __init__(self, question: str, example_workflow: str = "", prompt_string: str = ""):
        super().__init__(question, example_workflow, prompt_string)


class PythonCodingAgent(ReActRuntime):
    def __init__(self, api_key: str, model: str, question: str, temperature: float = 0.7, safety_settings: Any = None, max_output_tokens: int = None):
        llm = PythonCodingLLM(api_key=api_key, model=model, temperature=temperature, safety_settings=safety_settings, max_output_tokens=max_output_tokens)
        prompt = PythonCodingPrompt(question=question, example_workflow="", prompt_string="")
        tools = ToolKit([PythonRuntimeTool(description="Run python code", tool_name="python_runtime_tool")])
        super().__init__(llm, prompt, tools)
        
    def loop(self, agent_max_steps: int = 5, verbose_tools: bool = False) -> str:
        return super().loop(agent_max_steps, verbose_tools)