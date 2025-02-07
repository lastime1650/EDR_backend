# LLM 세션 관리 , 'instance id'를 기반으로 사용.

import threading
from typing import Optional, Any




class LLM_Session_class():
    def __init__(self):

        self.sessions = {
            "main_mutex": threading.Lock(),  # 자원 동기화
            "LLM_sessions": []
        }

        Example1 = '''
        [
            {
                "Instance_ID": "ABC,,,",
                "LLM":
                    {
                        "TYPE_EVAL": 실제 LLM 인스턴스 객체,
                        "MIDDLE_EVAL": 실제 LLM 인스턴스 객체,
                        "FINAL_EVAL": 실제 LLM 인스턴스 객체
                    }
            },,,
        ]
        '''

    # 현재 존재하는 세션 가져오기
    def Get_Session(self, LLM_TYPE:LLM_Type, Instance_ID:str)->Optional[Any]:
        with self.sessions["main_mutex"]:
            for session_json in self.sessions["LLM_sessions"]:
                if session_json["Instance_ID"] == Instance_ID:
                    return session_json["LLM"][LLM_TYPE.name]
            return None

    # 세션 추가
    def Add_Session(self, LLM_TYPE:LLM_Type, Instance_ID:str, LLM_instance:Any)->bool:
        return True

    # Remove Session