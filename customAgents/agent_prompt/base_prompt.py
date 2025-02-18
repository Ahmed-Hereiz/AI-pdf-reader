from PIL import Image
from typing import Union
import os


class BasePrompt:
    def __init__(self, text: str = "", image: Union[str, Image.Image, None] = None):
        """
        Initializes the BasePrompt with the given template file and prompt string.

        :param text: The text to be associated with the prompt.
        :param image: An optional image to be associated with the prompt. Can be a file path or a PIL Image object.
        """

        self.text = self._load_text(text)
        self.image = self._load_image(image)
        self.prompt = ""

    def construct_prompt(self, placeholder_dict: dict = {}, query: str = ""):
        """
        Method for interfacing with runtime (used inside the runtime class), integrating text and image.
        This needs to be overwritten inside every inherited class for being customizable for the use case.
        """
        self.prompt += self.text

        for key, value in placeholder_dict.items():
            self.replace_placeholder(f"{key}", value)

        self.append_to_prompt(query)

        if self.image:
            self.prepend_to_prompt("An image is provided with this prompt. Consider it in your response if relevant.\n")

        return self.prompt
    
    def _load_image(self, image: Union[str, Image.Image, None]) -> Union[Image.Image, None]:
        """
        Loads an image from a file path or returns the PIL Image object if already loaded.

        :param image: A file path to an image or a PIL Image object.
        :return: A PIL Image object or None if no image is provided.
        """
        if isinstance(image, str) and os.path.isfile(image):
            return Image.open(image)
        elif isinstance(image, Image.Image):
            return image
        return None

    def _load_text(self, text: str) -> str:
        """
        Loads text from a given string.

        :param text: A string to be used as text.
        :return: The provided text string.
        """
        return text

    def __repr__(self) -> str:
        """
        Returns a string representation of the BasePrompt instance for debugging.

        :return: A string representation of the instance.
        """
        if self.prompt == "":
            return "Prompt is not constructed yet."
        return f"BasePrompt initialized with prompt: \n\n{self.prompt}"

    def __str__(self) -> str:
        """
        Returns a user-friendly string representation of the BasePrompt instance.

        :return: A string representation of the instance.
        """
        if self.prompt == "":
            return "Prompt is not constructed yet."
        return f"BasePrompt initialized with prompt: \n\n{self.prompt}"

    def __add__(self, other) -> str:
        """
        Concatenates the prompt string of this instance with another BasePrompt instance.

        :param other: Another BasePrompt instance.
        :return: The concatenated prompt strings.
        """
        if isinstance(other, BasePrompt):
            return self.prompt + '\n' + other.prompt
        return NotImplemented

    def replace_placeholder(self, placeholder: str, value: str):
        """
        Replaces a placeholder in the prompt string with a given value.

        :param placeholder: The placeholder string to be replaced.
        :param value: The value to replace the placeholder with.
        """
        self.prompt = self.prompt.replace(placeholder, value)

    def append_to_prompt(self, additional_text: str):
        """
        Appends additional text to the end of the prompt.

        :param additional_text: The text to be appended to the prompt.
        """
        if additional_text:
            self.prompt += '\n' + additional_text

    def prepend_to_prompt(self, additional_text: str):
        """
        Prepends additional text to the beginning of the prompt.

        :param additional_text: The text to be prepended to the prompt.
        """
        if additional_text:
            self.prompt = additional_text + '\n' + self.prompt
    
    def clear_prompt(self):
        """
        Clears the current prompt, resetting it to an empty string.
        """
        self.prompt = ""

    def set_image(self, image: Union[str, Image.Image]):
        """
        Sets or updates the image associated with the prompt.

        :param image: The image to be associated with the prompt. Can be a file path or a PIL Image object.
        """
        self.image = self._load_image(image)

    def get_prompt(self) -> str:
        """
        Returns the current prompt string.

        :return: The current prompt string.
        """
        return self.prompt

    def has_image(self) -> bool:
        """
        Checks if an image is associated with the prompt.

        :return: True if an image is associated, False otherwise.
        """
        return self.image is not None

    def reset(self):
        """
        Resets the BasePrompt instance to its initial state.
        """
        self.clear_prompt()
        self.image = None
        self.text = ""

    def update_text(self, new_text: str):
        """
        Updates the text associated with the prompt.

        :param new_text: The new text to be associated with the prompt.
        """
        self.text = self._load_text(new_text)

    def get_image(self) -> Union[Image.Image, None]:
        """
        Returns the current image associated with the prompt.

        :return: The current image or None if no image is associated.
        """
        return self.image

    def prompt_length(self) -> int:
        """
        Returns the length of the current prompt string.

        :return: The length of the prompt string.
        """
        return len(self.prompt)

