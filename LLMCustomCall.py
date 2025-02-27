from typing import Any
from PIL.Image import Image
from customAgents.agent_llm import BaseLLM, BaseMultiModal
import google.generativeai as genai
import pathlib


class TextLLM(BaseLLM):
    def __init__(self, api_key: str, model: str, temperature: float, safety_settings: Any = None, parser: Any = ..., initialize_verbose: bool = False, max_tokens: int | None = None, top_p: float | None = None, top_k: int | None = None, frequency_penalty: float | None = None, presence_penalty: float | None = None, *args: Any, **kwargs: Any):
        super().__init__(api_key, model, temperature, safety_settings, parser, initialize_verbose, max_tokens, top_p, top_k, frequency_penalty, presence_penalty, *args, **kwargs)

    def llm_generate(self, input: str):
        if self._chain is None:
            raise ValueError("LLM Chain is not initialized from TextLLM class.")
        
        for chunk in self._chain.stream(input=input):
            yield chunk


class ImageMultiModalLLM(BaseMultiModal):
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, safety_settings: Any = None, max_output_tokens: int = None):
        super().__init__(api_key, model, temperature, safety_settings, max_output_tokens)

    def multimodal_generate(self, prompt: str, image: Image | None = None, stream: bool = True):
        
        multimodal_message = self._make_message_content(prompt=prompt, image=image)
        if stream:
            response_generator = self._multi_modal.stream([multimodal_message])
            for chunk in response_generator:
                yield chunk.content
        else:
            response = self._multi_modal.invoke([multimodal_message])
            return response


class AudioMultiModal(BaseMultiModal):
    def __init__(self, api_key: str, model: str, temperature: float = 0.7, safety_settings: Any = None, max_output_tokens: int = None):
        super().__init__(api_key, model, temperature, safety_settings, max_output_tokens)

        genai.configure(api_key=api_key)
        self.audio_model = genai.GenerativeModel(model)

    def multimodal_generate(self, prompt, audio_file_path, stream: bool = True):
        audio_content = {
            "mime_type": "audio/mp3",
            "data": pathlib.Path(audio_file_path).read_bytes()
        }
        
        if stream:
            response = self.audio_model.generate_content([prompt, audio_content], stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        else:
            response = self.audio_model.generate_content([prompt, audio_content])
            return response.text
