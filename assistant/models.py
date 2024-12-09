from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_vertexai import ChatVertexAI
from typing import List, Dict, Any, Optional

class ModelManager:
    def __init__(self):
        # Initialize different models
        self.models = {
            "gpt-4-vision": ChatOpenAI(model="gpt-4-vision-preview", max_tokens=4096),
            "gpt-4o": ChatOpenAI(model="gpt-4"),
            "claude-3-sonnet": ChatAnthropic(model="claude-3-sonnet"),
            "gemini-pro": ChatVertexAI(model="gemini-pro"),
            "gemini-pro-vision": ChatVertexAI(model="gemini-pro-vision")
        }

    def get_model_for_task(self, files: List[Dict] = None) -> Any:
        """Select appropriate model based on content type and preference"""
        
        # If there are images, use an image model
        if files and any(f["type"] == "image" for f in files):
            return self.models["gpt-4o"]

        # Default to GPT-4 for text-only
        return self.models["gpt-4o-mini"]

model_manager = ModelManager()
get_model_for_task = model_manager.get_model_for_task