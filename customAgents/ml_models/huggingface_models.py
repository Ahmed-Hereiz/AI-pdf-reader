import cv2
import base64
import requests
import numpy as  np
from PIL import Image
from io import BytesIO
from customAgents.ml_models import BaseModels


class HFModels(BaseModels):
    def __init__(self, hugging_face_token: str, model_api_url: str):
        
        self._hugging_face_token = hugging_face_token
        self._model_api_url = model_api_url
        self._headers = {"Authorization": f"Bearer {self._hugging_face_token}"}

        super().__init__()

    def inference(self, input_dict: dict):

        response = requests.post(self._hugging_face_token, headers=self._headers, json=input_dict)
        
        if response.status_code == 200:
            return response.content
        else: 
            raise ValueError(f"Error: {response.status_code}, {response.text}")


class HFTxt2ImgModels(HFModels):
    def __init__(self, hugging_face_token: str, model_id: str="CompVis/stable-diffusion-v1-4"):

        stable_diffusion_api_url = f"https://api-inference.huggingface.co/models/{model_id}"

        super().__init__(hugging_face_token=hugging_face_token, model_api_url=stable_diffusion_api_url)


    def inference(self, inputs: str):

        data = {"inputs": inputs}
        response = requests.post(self._model_api_url, headers=self._headers, json=data)

        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            raise ValueError(f"Error: {response.status_code}, {response.text}")
        

class HFImg2ImgModels(HFModels):
    def __init__(self, hugging_face_token: str, model_id: str="timbrooks/instruct-pix2pix"):
        pix2pix_api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        super().__init__(hugging_face_token=hugging_face_token, model_api_url=pix2pix_api_url)

    def _convert_to_pil(self, image):
        if isinstance(image, np.ndarray): 
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image)  
        elif isinstance(image, Image.Image): 
            pil_image = image
        else:
            raise ValueError("Input must be a PIL image or an OpenCV image (NumPy array).")
        return pil_image

    def inference(self, image, prompt: str= ""):
        pil_image = self._convert_to_pil(image)

        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

        payload = {
            "inputs": prompt,
            "image": img_str,
        }

        headers = {
            "Authorization": f"Bearer {self._hugging_face_token}",
            "Content-Type": "application/json"
        }

        response = requests.post(self._model_api_url, json=payload, headers=headers)

        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else:
            raise ValueError(f"Error: {response.status_code}, {response.text}")


class HFImg2TxtModels(HFModels):
    def __init__(self, hugging_face_token: str, model_id: str="Salesforce/blip-image-captioning-base"):
        img2txt_api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        super().__init__(hugging_face_token=hugging_face_token, model_api_url=img2txt_api_url)

    def inference(self, image_path: str):
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()

        data = {
            "inputs": image_bytes
        }
        response = requests.post(self._model_api_url, headers=self._headers, data=data)
        if response.status_code == 200:
            return response.json() 
        else:
            raise ValueError(f"Error: {response.status_code}, {response.text}")


class HFSpeech2TxtModels(HFModels):
    def __init__(self, hugging_face_token: str, model_id: str="facebook/wav2vec2-large-960h"):
        speech2txt_api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        super().__init__(hugging_face_token=hugging_face_token, model_api_url=speech2txt_api_url)

    def inference(self, audio_path: str):
        with open(audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()

        data = {
            "inputs": audio_bytes
        }
        response = requests.post(self._model_api_url, headers=self._headers, data=data)
        if response.status_code == 200:
            return response.json()  
        else:
            raise ValueError(f"Error: {response.status_code}, {response.text}")


class HFTxt2SpeechModels(HFModels):
    def __init__(self, hugging_face_token: str, model_id: str="facebook/fastspeech2-en-ljspeech"):
        txt2speech_api_url = f"https://api-inference.huggingface.co/models/{model_id}"
        super().__init__(hugging_face_token=hugging_face_token, model_api_url=txt2speech_api_url)

    def inference(self, text: str):
        data = {"inputs": text}
        response = requests.post(self._model_api_url, headers=self._headers, json=data)
        if response.status_code == 200:
            return response.content
        else:
            raise ValueError(f"Error: {response.status_code}, {response.text}")


