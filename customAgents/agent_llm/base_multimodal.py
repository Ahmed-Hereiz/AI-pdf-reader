from colorama import Fore, Style
from typing import Any, List, Union
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.schema import HumanMessage, AIMessage
import io
import base64
import warnings

warnings.filterwarnings("ignore")

class BaseMultiModal:
    def __init__(
            self,
            api_key: str,
            model: str,
            temperature: float = 0.7,
            safety_settings: Any = None,
            max_output_tokens: int = None
        ):
        
        self._api_key = api_key
        self._model = model
        self._temperature = temperature
        self._safety_settings = safety_settings
        self._max_output_tokens = max_output_tokens
        self._multi_modal = self._initialize_multimodal()

    def _initialize_multimodal(self):
        if self._model.startswith("gemini"):  # Google models
            return ChatGoogleGenerativeAI(
                model=self._model,
                google_api_key=self._api_key,
                temperature=self._temperature,
                max_output_tokens=self._max_output_tokens,
                convert_system_message_to_human=True
            )
        elif self._model.startswith("gpt"):  # OpenAI models
            return ChatOpenAI(
                model=self._model,
                openai_api_key=self._api_key,
                temperature=self._temperature,
                max_tokens=self._max_output_tokens
            )
        elif self._model.startswith("claude"):  # Anthropic models
            return ChatAnthropic(
                model=self._model,
                anthropic_api_key=self._api_key,
                temperature=self._temperature,
                max_tokens_to_sample=self._max_output_tokens
            )
        else:
            raise ValueError('Model not supported. Currently supported models: gemini, gpt, claude')

    def multimodal_generate(self, prompt: str, image: Union[Image.Image, None] = None, stream: bool = False, output_style: str = 'default') -> str:

        content = [{"type": "text", "text": prompt}]
        
        if image:
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            img_data = {
                "type": "image_url",
                "image_url": f"data:image/png;base64,{img_str}"
            }
            content.append(img_data)

        multimodal_message = HumanMessage(content=content)

        if stream:
            response_generator = self._multi_modal.stream([multimodal_message])
            full_response = ""
            for chunk in response_generator:
                chunk_text = chunk.content
                full_response += chunk_text
                if output_style != 'default':
                    self._print_colorized_output(chunk=chunk_text, output_style=output_style)
                else:
                    print(chunk_text, end="", flush=True)
            return full_response
        else:
            response = self._multi_modal.invoke([multimodal_message])
            if isinstance(response, AIMessage):
                response_text = response.content
            else:
                response_text = str(response)
            
            if output_style != 'default':
                self._print_colorized_output(chunk=response_text, output_style=output_style)
            return response_text

    def _print_colorized_output(self, chunk: str, output_style: str) -> None:
        """
        Method for customizing output color

        :param chunk: the output that needs to be printed.
        :param output_style: the color of the output.
        """
        allowed_styles = self.available_text_colors

        if output_style not in allowed_styles:
            raise ValueError(f"Invalid output style. Choose from {allowed_styles}")

        color_map = {
            "default": "",
            "green": Fore.LIGHTGREEN_EX,
            "blue": Fore.LIGHTBLUE_EX,
            "yellow": Fore.LIGHTYELLOW_EX,
            "cyan": Fore.LIGHTCYAN_EX,
            "red": Fore.LIGHTRED_EX,
            "magenta": Fore.LIGHTMAGENTA_EX
        }

        print(f"{color_map[output_style]}{chunk}{Style.RESET_ALL}", end='', flush=True)

    def __str__(self) -> str:
        multimodal_initialized = self._multi_modal is not None
        return f"Model used: {self._model}, with temperature: {self._temperature}, multimodal initialized: {multimodal_initialized}"

    @property
    def multimodal(self) -> Any:
        return self._multi_modal

    @property
    def available_text_colors(self) -> List[str]:
        return ['default', 'green', 'blue', 'yellow', 'cyan', 'red', 'magenta']

    def set_temperature(self, temperature: float) -> None:
        """
        Set a new temperature for the model.

        :param temperature: The new temperature value (0.0 to 1.0).
        """
        if 0.0 <= temperature <= 1.0:
            self._temperature = temperature
            self._multi_modal = self._initialize_multimodal()
        else:
            raise ValueError("Temperature must be between 0.0 and 1.0")

    def set_max_output_tokens(self, max_tokens: int) -> None:
        """
        Set a new maximum output token limit.

        :param max_tokens: The new maximum number of output tokens.
        """
        if max_tokens > 0:
            self._max_output_tokens = max_tokens
            self._multi_modal = self._initialize_multimodal()
        else:
            raise ValueError("Max output tokens must be a positive integer")

    def reset_model(self) -> None:
        """
        Resets the model to its initial state.
        """
        self._multi_modal = self._initialize_multimodal()

    def get_model_info(self) -> str:
        """
        Returns a string containing information about the model.
        """
        return f"Model: {self._model}, Temperature: {self._temperature}, Max Output Tokens: {self._max_output_tokens}"

    def change_safety_settings(self, new_settings: Any) -> None:
        """
        Update the safety settings for the model.

        :param new_settings: The new safety settings to apply.
        """
        self._safety_settings = new_settings
        self._multi_modal = self._initialize_multimodal()
