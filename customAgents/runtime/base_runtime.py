import json
from typing import Union
from customAgents.agent_llm import BaseLLM, BaseMultiModal
from customAgents.agent_prompt import BasePrompt
from customAgents.agent_tools import ToolKit


class BaseRuntime:
    def __init__(self, llm: Union[BaseLLM, BaseMultiModal], prompt: BasePrompt, toolkit: ToolKit):
        """
        Initializes the BaseRuntime with the given LLM, prompt, and tools.

        :param llm: The language model to be used.
        :param prompt: The prompt for the agent.
        :param tools: Tools that assist the agent.
        """
        self.llm = llm
        self.prompt = prompt
        self.toolkit = toolkit


    def step(self, query=None) -> str:
        """
        Generates a response from the LLM using the current agent prompt.

        :raises ValueError: If the LLM or agent prompt is not properly initialized.
        :return: The generated response as a string.
        """
        if not self.llm or not self.prompt:
            raise ValueError("LLM or agent prompt is not properly initialized.")
        if isinstance(self.llm, BaseLLM):
            if query is not None:
                input_query = self.prompt.prompt + f"\n{query}"
            else:
                input_query = self.prompt.prompt
            response = self.llm.llm_generate(input=input_query)
            return response
        elif isinstance(self.llm, BaseMultiModal):
            if query is not None:
                input_query = self.prompt.prompt = f"\n{query}"
            else:
                input_query = self.prompt.prompt
            if self.prompt.image is None:
                response = self.llm.multimodal_generate(prompt=input_query)
            else:
                response = self.llm.multimodal_generate(prompt=input_query,img=self.prompt.image)
            return response


    def loop(self, n_steps: int = 1, query: str = None) -> str:
        """
        Continuously generates responses for a specified number of steps.

        :param n_steps: The number of steps to generate responses for.
        :return: The final response generated after the specified number of steps.
        """
        for _ in range(n_steps):
            response = self.step(query=query)
            self.prompt.prompt += f"\n{response}"

        return response
    

    def _extract_json_from_string(self, text: str):
        """
        Extracts JSON objects from a string.

        :param text: Input string that may contain JSON objects
        :return: List of extracted JSON objects
        """
        json_objects = []
        brace_stack = []
        json_str = ""
        inside_json = False

        for _, char in enumerate(text):
            if char == '{':
                brace_stack.append(char)
                inside_json = True
            if inside_json:
                json_str += char
            if char == '}':
                brace_stack.pop()
                if not brace_stack:
                    inside_json = False
                    try:
                        json_object = json.loads(json_str)
                        json_objects.append(json_object)
                    except json.JSONDecodeError:
                        pass
                    json_str = ""

        return json_objects

    def reset(self) -> None:
        """
        Resets the runtime state by clearing the prompt.
        """
        self.prompt.prompt = ""
        self.prompt.img = None

    def update_prompt(self, new_prompt: str) -> None:
        """
        Updates the current prompt with new text.

        :param new_prompt: The new prompt text to set
        """
        self.prompt.prompt = new_prompt

    def add_to_prompt(self, additional_text: str) -> None:
        """
        Appends additional text to the current prompt.

        :param additional_text: Text to append to the current prompt
        """
        self.prompt.prompt += additional_text

    def get_toolkit_info(self) -> dict:
        """
        Returns information about available tools in the toolkit.

        :return: Dictionary containing tool information
        """
        return {
            "available_tools": self.toolkit.list_tools(),
            "tool_count": len(self.toolkit.list_tools())
        }

    def __str__(self) -> str:
        """
        Returns a string representation of the runtime.

        :return: String describing the runtime state
        """
        return f"BaseRuntime(llm={type(self.llm).__name__}, prompt_length={len(self.prompt.prompt)}, tools={len(self.toolkit.list_tools())})"