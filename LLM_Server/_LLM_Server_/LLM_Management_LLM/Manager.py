# LLM 을 총괄하는 모듈


#--
#----
# LLM 랭체인에서 프로세스 행위에 대하여 맥락을 분석함
from typing import Dict, Optional, Tuple

from langchain.chat_models import ChatOpenAI

import threading
#--

from _LLM_Server_.LLM_Management_LLM.LLM_clustering.LLM_Cluster import LLM_Cluster

# (중간, 최종, 사후_질의응답) ALL_EVAL 인스턴스
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL._2_ALL.ALL_Eval import ALL_Eval

# enum
from _LLM_Server_.llm_enum import LLM_req_Type

class LLM_Manager():
    def __init__(self):
        # LLM 클러스터 인스턴스
        self.LLM_cluster = LLM_Cluster()
        # LLM EVAL 인스턴스
        self.ALL_EVAL = ALL_Eval()


    # 인스턴스 모니터링 데이터 평가
    def Start_Evaluation(self, cmd:LLM_req_Type, Input:str, instance_id:str)->Tuple[bool, str]:
        # 세션 존재 여부 확인

        # 사용가능한 LLM 자원 탐색
        available_LLM = self.LLM_cluster.Get_Model()
        if not available_LLM:
            return False, "사용가능한 LLM이 없습니다."

        # core-server에서의 요청에 따른 평가 실행
        if cmd.name == "MIDDLE_EVAL" or cmd.name == "FINAL_EVAL" or cmd.name == "TYPE_EVAL":
            #return False, "현재 테스트 입니다. Eval 실행안함"
            with available_LLM["mutex"]:
                output = self.ALL_EVAL.Start_Evaluation(cmd, available_LLM["MODEL"],  instance_id, Input)
                available_LLM["reference_count"] -= 1  # 모델 참조 감소
                return output
        else:
            return False, "아직 지원하지 않는 평가 요청입니다."

    # 웹 소켓 챗봇
    def Start_Agent_Chatbot(self, Chatbot_Session_ID:str, Input_string:str, Current_Page:str)->Tuple[bool, str]:
        # 사용가능한 LLM 자원 탐색
        available_LLM = self.LLM_cluster.Get_Model()
        if not available_LLM:
            return False, "사용가능한 LLM이 없습니다."

        # 에이전트 시작
        with available_LLM["mutex"]:
            output = self.ALL_EVAL.Start_Agent_Chatbot(available_LLM["MODEL"], Chatbot_Session_ID, Input_string, Current_Page)
            available_LLM["reference_count"] -= 1  # 모델 참조 감소
            return output

