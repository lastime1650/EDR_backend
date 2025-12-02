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
                    google_api_key="****"
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
                    google_api_key="****"
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

    def Add_Model(self, model_name: str, model: Any):
        with self.mutex_:
            if model_name in self.LLMs:
                return False  # 이미 존재함
            self.LLMs[model_name] = {
                "model": model,
                "ref_count": 0,
                "mutex": threading.Lock()
            }
            return True

    def Remove_Model(self, model_name: str):
        with self.mutex_:
            if model_name not in self.LLMs:
                return False
            if self.LLMs[model_name]["ref_count"] > 0:
                return False  # 사용 중인 모델은 삭제 불가
            
            del self.LLMs[model_name]
            return True
