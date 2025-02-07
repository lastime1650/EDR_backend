import threading
from typing import Tuple, Dict, Optional, Any, List

from langchain.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatOpenAI
from langchain_core.tools import Tool

# 프롬프트 생성기
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Prompt.Prompt_Maker import Prompt_Maker

import requests

from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Share_converstaion_mem import Agent_Chatbot_Memory
# LLM 서버 내부용 enum
from _LLM_Server_.llm_enum import LLM_req_Type

# LLM 실질 요청 모듈
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL._Evaluation_main_logic_.main_logic import LLM_Agent_start

# Tools 모듈
from _LLM_Server_.EDR_AGENT_LLM.Tools.agent_tools import Make_Agent_tools

# WebSocket 관리 모듈
from _EDR_WebServer_.WebSocket_management.WebSocket_Manager import WebSocketManager

class Agent_Chatbot_manager():
    def __init__(self, core_server_ip:str, core_server_port:int=5070):
        self.main_core_server_url = f"http://{core_server_ip}:{core_server_port}"

        # 웹 서버와 세션중인 WebSocket관리 모듈
        self.WebSocket_Manager = WebSocketManager()

        # 에이전트 Tool 클래스
        self.Make_Agent_tools = Make_Agent_tools(core_server_ip, core_server_port, self.WebSocket_Manager)

    def Start_Chatbot(
            self,

            LLM_Model_obj:Any, # 사용할 LLM 모델

            Chatbot_Session_ID:str, # 대화 세션

            Input_String:str, #사용자 입력 문자열

            Current_Page:str, # 현재 사용자가 접속한 페이지

            Conversation_Manager_obj:Agent_Chatbot_Memory, # 대화 메모리 관리 인스턴스

    )->Tuple[bool, str]:

        # 입력 폼 생성
        query = f'''{{"Current_Page":"{Current_Page}" ,"SESSION_ID": "{Chatbot_Session_ID}" , "query_input": "{Input_String}"}}'''
        
        # 프롬프트 생성
        prompt = Prompt_Maker().Make_Prompt(LLM_req_Type.CHATBOT, Chatbot_Session_ID)

        # 도구 등록
        agent_tools:List[Tool] = self.Make_Agent_tools.Output_Tools()

        # 대화 메모리 버퍼 가져오기 및 생성 후 가져오기 * HDD에 저장하지 않는다.
        Conversation_buff = Conversation_Manager_obj.Get_Conversation(Chatbot_Session_ID, is_from_hdd=False)
        if not Conversation_buff:
            Conversation_buff = Conversation_Manager_obj.Create_ChatSession(Chatbot_Session_ID)

        return LLM_Agent_start(
            LLM_Model_obj=LLM_Model_obj,

            Prompt=prompt,

            Conversation_buff=Conversation_buff,

            Agent_tools=agent_tools
        ).Query(query)

