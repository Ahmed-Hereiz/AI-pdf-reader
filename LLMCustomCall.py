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



if __name__ == "__main__":
    # Load config from llm.json
    import json
    with open('llm.json', 'r') as f:
        config = json.load(f)
        api_key = config['api_key']
        model_config = config.get('model_config', {})

    # Test TextLLM
    text_llm = TextLLM(
        api_key=api_key,
        model=model_config.get('text_model', 'gemini-pro'),
        temperature=model_config.get('temperature', 0.7)
    )
    
    # Test text generation
    prompt = "Write a short poem about artificial intelligence."
    print("\nTesting TextLLM:")
    for response in text_llm.llm_generate(prompt):
        print(response, end="")
    print("\n")

    # Test ImageMultiModalLLM
    image_llm = ImageMultiModalLLM(
        api_key=api_key,
        model=model_config.get('image_model', 'gemini-pro-vision'),
        temperature=model_config.get('temperature', 0.7)
    )
    
    # Test image analysis (you would need an actual image file)
    print("Testing ImageMultiModalLLM:")
    try:
        from PIL import Image
        image = Image.open("path_to_test_image.jpg")
        prompt = "Describe what you see in this image."
        for response in image_llm.multimodal_generate(prompt, image):
            print(response, end="")
    except Exception as e:
        print(f"Image test skipped: {str(e)}")
    print("\n")

    # Test AudioMultiModal
    audio_llm = AudioMultiModal(
        api_key=api_key,
        model=model_config.get('audio_model', 'gemini-pro'),
        temperature=model_config.get('temperature', 0.7)
    )
    
    # Test audio analysis (you would need an actual audio file)
    print("Testing AudioMultiModal:")
    try:
        prompt = "Transcribe and analyze this audio."
        audio_path = "path_to_test_audio.mp3"
        for response in audio_llm.multimodal_generate(prompt, audio_path):
            print(response, end="")
    except Exception as e:
        print(f"Audio test skipped: {str(e)}")

