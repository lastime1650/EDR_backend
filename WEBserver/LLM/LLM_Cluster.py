import threading
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI

class LLM_Cluster():
    def __init__(self):
        self.mutex_ = threading.Lock()
        self.LLMs = {
            "default": {
                "model": ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                    google_api_key="AIzaSyBsbshtqhFk8syGxUAeF1SLKoc43BlJjc4"
                ),
                "ref_count": 0,
                "mutex": threading.Lock()
            },
            "default2": {
                "model": ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash",
                    temperature=0,
                    max_tokens=None,
                    timeout=None,
                    max_retries=2,
                    google_api_key="AIzaSyB39jFmNgJAZK6OeJrbu9FpTKFCe9fO1QM"
                ),
                    "ref_count": 0,
            "mutex": threading.Lock()
            }
        }

    # 모델 가져오기
    def Get_Model(self)->(Optional[str], Optional[Any]):
        with self.mutex_:
            for model_name, model_info in self.LLMs.items():
                if model_info["ref_count"] == 0:
                    model_info["ref_count"] += 1
                    return model_name, model_info["model"]
            return None, None
        
    # 모델 반환하기
    def Release_Model(self, model_name:str):
        with self.mutex_:
            for model_name, model_info in self.LLMs.items():
                if model_name == model_name:
                    if model_info["ref_count"] > 0:
                        model_info["ref_count"] -= 1
                        return True
                    else:
                        return False

    def Add_Model(self):
        pass

    def Remove_Model(self):
        pass