from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BaseModels(ABC):
    def __init__(self, model_type: Optional[str] = None, model_params: Optional[Dict[str, Any]] = None):
        self.model_type = model_type
        self.model_params = model_params or {}
        self.model = None

    @abstractmethod
    def load_model(self) -> None:
        """Load the model. This method should be implemented by subclasses."""
        pass

    @abstractmethod
    def inference(self, input_data: Any) -> Any:
        """
        Implement the model inference logic here.
        
        Args:
            input_data: The input data for the model.

        Returns:
            The output of the model inference.
        """
        pass

    def preprocess(self, input_data: Any) -> Any:
        """
        Preprocess the input data before inference.
        
        Args:
            input_data: The raw input data.

        Returns:
            The preprocessed input data.
        """
        return input_data

    def postprocess(self, output: Any) -> Any:
        """
        Postprocess the model output.
        
        Args:
            output: The raw output from the model.

        Returns:
            The postprocessed output.
        """
        return output

    def __str__(self) -> str:
        return f"BaseModels(model_type={self.model_type}, model_params={self.model_params})"

    def __repr__(self) -> str:
        return self.__str__()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dict containing model type, parameters and other metadata
        """
        return {
            "model_type": self.model_type,
            "model_params": self.model_params,
            "model_loaded": self.model is not None
        }

    def reset(self) -> None:
        """
        Reset the model to initial state.
        """
        self.model = None

    def validate_input(self, input_data: Any) -> bool:
        """
        Validate that input data meets model requirements.
        
        Args:
            input_data: Input data to validate

        Returns:
            bool indicating if input is valid
        """
        return True

    def save_model(self, path: str) -> None:
        """
        Save the model to disk.
        
        Args:
            path: Path to save model
        """
        raise NotImplementedError("save_model() not implemented for base class")

    def get_model_parameters(self) -> Dict[str, Any]:
        """
        Get the model's parameters.
        
        Returns:
            Dict of parameter names and values
        """
        if self.model is None:
            return {}
        return self.model_params or {}