from typing import Any, Dict, Optional
import joblib
from customAgents.ml_models.base_models import BaseModels

class SklearnModels(BaseModels):
    def __init__(self, model_path: str, model_type: Optional[str] = None, model_params: Optional[Dict[str, Any]] = None):
        super().__init__(model_type, model_params)
        self.model_path = model_path
        
    def load_model(self) -> None:
        try:
            self.model = joblib.load(self.model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load model from {self.model_path}: {str(e)}")

    def inference(self, input_data: Any) -> Any:
        if self.model is None:
            self.load_model()
            
        processed_input = self.preprocess(input_data)
        predictions = self.model.predict(processed_input)
        return self.postprocess(predictions)
