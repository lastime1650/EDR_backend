from enum import Enum
class LLM_req_Type(Enum):
    TYPE_EVAL = 1 # 유형 평가 # 메모리가 필요없다.

    MIDDLE_EVAL = 2 # 중간 평가 # 메모리가 필요하다
    FINAL_EVAL = 3 # 최종 평가 # 메모리가 필요하다

    QUESTION = 4 # 사후_질의응답

    CHATBOT = 5 # 챗봇 요청