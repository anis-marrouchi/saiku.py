from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union

class PredictionRequest:
    def __init__(self, prompt: Optional[str] = None, max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None, top_p: Optional[float] = None,
                 model: Optional[str] = None, meta: Optional[Dict[str, Any]] = None, **kwargs):
        self.prompt = prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.model = model
        self.meta = meta
        self.extra_args = kwargs

class PredictionResponse:
    def __init__(self, text: Union[str, Any], model: str, other_metadata: Optional[Any] = None):
        self.text = text
        self.model = model
        self.other_metadata = other_metadata

class LLM(ABC):
    @abstractmethod
    def interact(self, use_delegate: Optional[bool] = False) -> Union[str, None]:
        pass

    @abstractmethod
    def predict(self, request: PredictionRequest) -> PredictionResponse:
        pass