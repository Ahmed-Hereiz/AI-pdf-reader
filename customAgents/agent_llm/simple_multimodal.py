from typing import Any, Optional
from PIL import Image
from customAgents.agent_llm import BaseMultiModal


class SimpleMultiModal(BaseMultiModal):
    def __init__(
        self,
        api_key: str,
        model: str,
        temperature: float = 0.7,
        safety_settings: Any = None,
        max_output_tokens: Optional[int] = None
    ):
        """Uses default BaseMultiModal generate method"""

        super().__init__(
            api_key,
            model,
            temperature,
            safety_settings,
            max_output_tokens
        )

    def multimodal_generate(self, prompt: str, img: Image, stream: bool = False, output_style: str = 'default'):
        return super().multimodal_generate(prompt, img, stream, output_style)

    def set_safety_settings(self, new_settings: Any) -> None:
        """
        Update the safety settings for the model.

        :param new_settings: The new safety settings to apply.
        """
        self._safety_settings = new_settings
        self._multi_modal = self._initialize_multimodal()

    def get_safety_settings(self) -> Any:
        """
        Returns the current safety settings of the model.
        """
        return self._safety_settings

    def reset_temperature(self) -> None:
        """
        Resets the temperature to the default value (0.7).
        """
        self._temperature = 0.7
        self._multi_modal = self._initialize_multimodal()
        print("Temperature reset to default value of 0.7.")
