import threading

Prompt_System_Message = ""

# 전체(중간, 최종) 평가

from typing import Any, Optional, List, Dict, Tuple

import json

# 기본 LLM 대화형
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL._Evaluation_main_logic_.main_logic import LLM_eval_start, LLM_Chat_start
# 대화 메모리 공유 클래스
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Share_converstaion_mem import \
    Share_ConversationMemory, Agent_Chatbot_Memory
# 채팅 전용 메모리
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Chat_ConversationMemory import Chat_Memory_ConversationManager
# 챗봇 전용
from _LLM_Server_.EDR_AGENT_LLM.edr_agent_llm import Agent_Chatbot_manager

# 프롬프트 생성
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Prompt.Prompt_Maker import Prompt_Maker

# enum
from _LLM_Server_.llm_enum import LLM_req_Type

from langchain.memory import ConversationBufferMemory



# 중간평가 + 최종평가 + 사후_사용자간_질의응답 ---> 3가지가 가능한 클래스
class ALL_Eval():
    def __init__(self):
        self.Share_Conversation_Manager = Share_ConversationMemory()
        self.Share_Chat_Memory_Manager = Chat_Memory_ConversationManager(self.Share_Conversation_Manager)
        self.Share_Agent_Chatbot_Memory_Manager = Agent_Chatbot_Memory()

        # 챗봇 에이전트 클래스
        self.Agent_Chatbot_manager = Agent_Chatbot_manager("192.168.0.1")


    def Start_Evaluation(
            self,
            LLM_Eval_Type: LLM_req_Type,

            LLM_Model_obj: Any,


            Conversation_ID:str,

            Input:str,
    )->Tuple[bool,str]:

        # 최종 요청 질의값 생성
        '''
            Request_Data = {
                "TYPE": str(LLM_Eval_Type.name),
                "Input": Input
            }
        '''
        Request_Data = self.Make_Request_Sentence(LLM_Eval_Type, Input)
        if not Request_Data:
            return False, "Make_Request_Sentence 실패"

        # 프롬프트 객체 생성 ( Eval Type에 따라 프롬프트가 다르다 )
        Prompt = Prompt_Maker().Make_Prompt(LLM_Eval_Type, Conversation_ID)

        # LLM에게 요청
        return LLM_eval_start(
            LLM_Eval_Type = LLM_Eval_Type,
            LLM_Model_obj=LLM_Model_obj,

            Prompt=Prompt,

            Conversation_ID=Conversation_ID,
            Conversation_manager_obj=self.Share_Conversation_Manager
        ).Query(Request_Data)


    def Start_Agent_Chatbot(self, LLM_Model_obj:Any, Chatbot_Session_ID:str, Input:str, Current_Page:str)->Tuple[bool, str]:
        # 이 에이전트는 다른 전용 모듈에서 구현되었다.
        return self.Agent_Chatbot_manager.Start_Chatbot(
            LLM_Model_obj=LLM_Model_obj,
            Chatbot_Session_ID=Chatbot_Session_ID,
            Input_String=Input,
            Current_Page=Current_Page,
            Conversation_Manager_obj=self.Share_Agent_Chatbot_Memory_Manager
        )

    ############################


    def Make_Request_Sentence(self, LLM_Eval_Type:LLM_req_Type, Input:str)->Optional[str]:
        # 쿼리문 작성
        Req_JSON = {
            "TYPE": str(LLM_Eval_Type.name),
            "Input": Input
        }

        json_to_str = json.dumps(Req_JSON,ensure_ascii=False)

        return json_to_str

