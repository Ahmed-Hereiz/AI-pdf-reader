"""
This module provides the necessary classes for working with various types of Language Learning Models (LLMs) and multimodal models.
It includes base classes and simple implementations for both single and multimodal tasks.

Classes:
- BaseLLM: The base class for all language models, providing common functionality and structure.
- SimpleLLM: A simple implementation of a language model.
- SimpleInvokeLLM: A variant of SimpleLLM that supports invocation.
- SimpleStreamLLM: A variant of SimpleLLM that supports streaming responses.
- BaseMultiModal: The base class for multimodal models, allowing interaction with both text and image inputs.
- SimpleMultiModal: A simple implementation of a multimodal model.

Usage:
Import the desired classes from this module to create and interact with language models and multimodal models.
"""

from .base_llm import BaseLLM
from .base_multimodal import BaseMultiModal
from .simple_llm import SimpleLLM, SimpleInvokeLLM, SimpleStreamLLM
from .simple_multimodal import SimpleMultiModal

__all__ = [
    'BaseLLM',          # Base class for all LLMs, providing common functionality.
    'SimpleLLM',       # Simple implementation of a language model.
    'SimpleInvokeLLM', # LLM that supports invocation.
    'SimpleStreamLLM', # LLM that supports streaming responses.
    'BaseMultiModal',   # Base class for multimodal models, allowing interaction with text and images.
    'SimpleMultiModal'  # Simple implementation of a multimodal model.
]

__doc__ = """
This module contains classes that define the structure and behavior of various language models and multimodal models.
It serves as the entry point for importing these classes into other parts of the application.
Refer to base_llm.py for the foundational LLM structure and base_multimodal.py for multimodal capabilities.
"""

__name__ = "customAgents.agent_llm"

__package__ = "customAgents"

__file__ = __file__

__path__ = __path__

__version__ = "1.0.0"  
