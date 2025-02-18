from customAgents.agent_prompt import BasePrompt
from typing import Union
from PIL import Image


class SimplePrompt(BasePrompt):
    def __init__(
        self, 
        text: str = "", 
        image: Union[str, Image.Image, None] = None
    ):
        """
        Initializes the SimplePrompt with the given text, image, and audio.

        :param text: The text to be associated with the prompt.
        :param image: An optional image to be associated with the prompt. Can be a file path or a PIL Image object.
        :param audio: An optional audio file path to be associated with the prompt or a pydub AudioSegment.
        """
        super().__init__(text, image)
