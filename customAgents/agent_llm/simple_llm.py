from typing import Any, Optional
from langchain_core.output_parsers import StrOutputParser
from customAgents.agent_llm import BaseLLM

class SimpleLLM(BaseLLM):
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        safety_settings: Any = None,
        parser: Any = StrOutputParser(),
        initialize_verbose: bool = False,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        *args: Any,
        **kwargs: Any
    ):
        """Uses default BaseLLM generate method"""
        super().__init__(
            api_key,
            model,
            temperature,
            safety_settings,
            parser,
            initialize_verbose,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            *args,
            **kwargs
        )

class SimpleInvokeLLM(SimpleLLM):
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        safety_settings: Any = None,
        parser: Any = StrOutputParser(),
        initialize_verbose: bool = False,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(
            api_key,
            model,
            temperature,
            safety_settings,
            parser,
            initialize_verbose,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            *args,
            **kwargs
        )

    def llm_generate(self, input: str) -> str:
        return self.invoke_response(input=input)

class SimpleStreamLLM(SimpleLLM):
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float,
        safety_settings: Any = None,
        parser: Any = StrOutputParser(),
        initialize_verbose: bool = False,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        frequency_penalty: Optional[float] = None,
        presence_penalty: Optional[float] = None,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(
            api_key,
            model,
            temperature,
            safety_settings,
            parser,
            initialize_verbose,
            max_tokens,
            top_p,
            frequency_penalty,
            presence_penalty,
            *args,
            **kwargs
        )

    def llm_generate(self, input: str) -> str:
        return self.generate_response(input=input)