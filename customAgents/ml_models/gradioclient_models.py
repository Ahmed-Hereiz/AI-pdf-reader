from customAgents.ml_models import BaseModels
from gradio_client import Client


class GradioClientModels(BaseModels):
    def __init__(self, gradio_client_id: str, api_name: str = None):
        self.gradio_client_id = gradio_client_id
        self.api_name = api_name
        self.client = None
        super().__init__()

    def load_model(self):
        self.client = Client(self.gradio_client_id)

    def inference(self, input_prompt):
        if self.client is None:
            self.load_model()

        client_output = self.client.predict(
            input_prompt,
            api_name=self.api_name,
        )

        return client_output
