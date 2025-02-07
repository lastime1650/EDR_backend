# LLM 클러스터링 로직
import time
from typing import Optional, List, Any, Dict

from langchain.chat_models import ChatOpenAI

import threading
#--

from enum import Enum
class Available_LLM_Models(Enum):
    chatgpt = 0

class LLM_Cluster():
    def __init__(self):
        '''
            지원가능한 LLM 모델 목록
        '''

        '''
            [[ self.LLM_sessions ]] @desc core-server의 'instance id'를 기반으로 사용하고 있는
        '''
        self.Remove_queue_mutex = threading.Lock()
        self.Remove_queue:List[str] = []

        self.LLM_info = {
            "main_mutex": threading.Lock(),  # LLM 자원 이동에 관한 동기화
            "LLM": {

                "default":{
                    "MODEL_TYPE": Available_LLM_Models["chatgpt"].name,
                    "METADATA": "EDR 기본 제공형 LLM모델", # default는 구지 추가 안함
                    "MODEL": ChatOpenAI(  # LLM 자원 ( default )
                        model="gpt-4o-mini",  # "gpt-4o-mini",  # 모델을 지정 (gpt-4o-mini)
                        temperature=0.8,  # 0.7,  # 응답 다양성 조절
                        openai_api_key="API-KEY",
                        # OpenAI API 키 설정
                    ),
                    "reference_count": 0,  # 참조 카운트 증가
                    "mutex": threading.Lock(),  # 자원 동기화


                }
            }
        }

    # 모델 가져오기/사용하기 ( ref count 참조 값이 증가된다. )
    # 랜덤하게 가져옴
    def Get_Model(self)->Optional[Dict]:
        current_minimum_ref_count = 0
        current_model_name = ""
        with self.LLM_info["main_mutex"]:
            # ref 카운트 가장 적은거 가져오기
            for model_name in self.LLM_info["LLM"]:
                if current_minimum_ref_count == 0 or self.LLM_info["LLM"][model_name]["reference_count"] < current_minimum_ref_count:
                    current_minimum_ref_count = self.LLM_info["LLM"][model_name]["reference_count"]
                    current_model_name = model_name

            if (current_model_name != ""):
                self.LLM_info["LLM"][model_name]["reference_count"] += 1
                return dict( self.LLM_info["LLM"][model_name] )
            else:
                return None


    # 참조 감소
    def Derefer_the_reference_count(self, LLM_NAME:str):
        with self.LLM_info["main_mutex"]:
            self.LLM_info["LLM"][LLM_NAME]["reference_count"] -= 1

    # 모델 추가하기
    def Add_Model(self, NAME:str, MODEL_TYPE:Available_LLM_Models, METADATA:dict) -> dict:
        output = {"status": "failed", "response": ""}
        '''
        /*
            <LLM_Model_Info> 정보는 {LLM_Model_Name}에 따라 다름

            < 현재 추가 가능한 LLM >
            1. chatgpt

        */
        {
            "MODEL_NAME": "",
            "METADATA": {} -> 불투명 하지만
        }

        '''
        with self.LLM_info["main_mutex"]:
            # 중복 검사
            if not( NAME in self.LLM_info["LLM"]):
                # MODEL_TYPE 일치 검사
                if MODEL_TYPE.name == Available_LLM_Models.chatgpt.name:
                    self.LLM_info["LLM"][NAME] = {
                        "MODEL_TYPE": MODEL_TYPE.name,
                        "METADATA": METADATA,
                        "MODEL": ChatOpenAI(  # LLM 자원 ( default )
                            model=METADATA["model"],#"gpt-4o-mini",  # 모델을 지정 (gpt-4o-mini)
                            temperature=float(METADATA["temperature"]),#0.7,  # 응답 다양성 조절
                            openai_api_key=METADATA["openai_api_key"],#"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"
                            # OpenAI API 키 설정
                        ),
                        "reference_count": 0,  # 참조 카운트 증가
                        "mutex": threading.Lock()  # 자원 동기화
                    }
                    output["status"] = "success"
                    output["response"] = "성공"
                    print(self.LLM_info["LLM"])
                    return output



                else:
                    output["response"] = "지원하지 않는 모델 타입입니다."
                    return output
            else:
                output["response"] = "이미 존재하는 ID/닉네임 입니다."
                return output


    def Remove_Model(self, LLM_NAME:str)-> dict:
        '''
        ' LLM_NAME ' 기반 제거
        '''
        with self.LLM_info["main_mutex"]:
            if LLM_NAME in self.LLM_info["LLM"]:
                if self.LLM_info["LLM"][LLM_NAME]["reference_count"] == 0:
                    del self.LLM_info["LLM"][LLM_NAME]
                    return {"status":"success", "response":"바로 삭제 되었습니다."}
                else:
                    # 바로 불가능하면 큐에 등록 (지연)
                    if not LLM_NAME in self.Remove_queue:
                        with self.Remove_queue_mutex:
                            self.Remove_queue.append(LLM_NAME)
                        return {"status":"success", "response":"현재 다른 곳에서 사용 중이므로, 삭제 대기 큐에 등록되었습니다."}
                    else:
                        return {"status":"fail", "response":"이미 삭제 대기 큐에 존재합니다."}
            else:
                return {"status":"fail", "response":"등록되지 않는 모델입니다."}

    # 삭제 스레드
    def _remove_model_loop(self):

        while True:
            time.sleep(1)
            # 삭제 요청 대기 큐에 있는 경우 제거
            with self.Remove_queue_mutex:
                if len(self.Remove_queue) > 0:

                    with self.LLM_info["main_mutex"]:
                        for LLM_NAME in self.Remove_queue:
                            if LLM_NAME in self.LLM_info["LLM"]:
                                if self.LLM_info["LLM"][LLM_NAME]["reference_count"] == 0:
                                    del self.LLM_info["LLM"][LLM_NAME]