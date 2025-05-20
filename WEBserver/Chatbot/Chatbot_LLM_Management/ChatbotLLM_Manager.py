import json
import threading
from typing import List, Optional, Dict

from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

# LLM 매니저
from LLM.LLMManager import LLM_Manager


# 에이전트 도구
from Chatbot.Chatbot_LLM_Management.ChatbotLLM_Tools import Chatbot_tools

class Chatbot_LLM_Manager():
    def __init__(self, ChatbotTools:Chatbot_tools, LLM_Manager:LLM_Manager):

        # 에이전트 도구
        self.tools = ChatbotTools


        self.LLM_Manager = LLM_Manager # LLM 요청
        self.chatbot_session = {}  # 대화 메모리
        self.mutex_ = threading.Lock()
        '''
        self.chatbot_session ={
            "hisotry_key/client_cookie_id": ConversationBufferMemory
        }
        '''

    # 대화 요청 ( 요청마다 LLM 클러스터로부터 할당받고 해야함 ) -> 이미 대화 메모리는 저장되어 있으므로 문제없음
    def Start_ChatBot(self, query:str, history_key:str)->str:
        Conversationbuffermemory = self.get_conversationbuffermemory_(history_key)

        output = self.LLM_Manager.Start_Agent_LLM(
            input_json={
                "input": query,
            },
            prompt=self.generate_prompt_(history_key),
            tools=self.tools.Output_Tools(), # 도구 전용 객체로부터 가져옴
            conversation_buffer=Conversationbuffermemory,
        )

        response_to_str = output["output"]

        # 만약 LLM이 JSON형식으로만 응답했다면, 정제처리
        try:
            response_to_str = json.loads( response_to_str.replace("Final Answer: ", "").replace("```json","").replace("```","").replace("\n","") )
            response_to_str = json.dumps(response_to_str, ensure_ascii=False)

        except:
            pass

        print(response_to_str)

        return response_to_str


    # 내장함수

    # 대화 메모리 버퍼 생성/등록
    def get_conversationbuffermemory_(self, history_key:str)->ConversationBufferMemory:
        with self.mutex_:
            if history_key not in self.chatbot_session:
                self.chatbot_session[history_key] = ConversationBufferMemory(
                                                        memory_key=history_key,
                                                        return_messages=True,
                                                    )
            return self.chatbot_session[history_key]

    def reset_conversationbuffermemory_(self, history_key:str): # 리셋
        with self.mutex_:
            if history_key in self.chatbot_session:
                del self.chatbot_session[history_key] # 삭제
                self.chatbot_session[history_key] = ConversationBufferMemory( # 새롭게 시작
                                                        memory_key=history_key,
                                                        return_messages=True,
                                                    )

    # 이전 대화 기록 가져오기
    def get_previous_chat_history_(self, history_key: str) -> List[Dict]:
        '''
            [반환형]
            메모리버퍼를 for문으로 읽고,
            List[Dict]형식으로
            [
                {
                    "ai": "이전 대화 내용",
                    "user": "이전 대화 사용자 이름"
                },, 순차적으로 가져와야함.
            ]
        '''
        # 메모리 버퍼 가져오기
        output = []
        with self.mutex_:
            if history_key in self.chatbot_session:
                conversation_buffer:ConversationBufferMemory = self.chatbot_session[history_key]

                # 한 dict에 묶어서 Human, AI 를 1쌍으로 묶어야함
                '''
                [
                    {
                        "user": ",,",
                        "ai": ",,
                    },,
                ]
                '''
                messsages = conversation_buffer.chat_memory.messages
                human_ai_pairs = list( zip(messsages[::2], messsages[1::2]) ) # 1쌍씩 묶음
                for human_msg, ai_msg in human_ai_pairs:
                    '''
                        [ 주의 사항 ]
                        Human의 메시지는 실제로는 JSON 형식으로 저장됨.
                        ->
                         {
                            "user":"헬로", // 이 값이 LLM 챗봇 대화의 값임
                            "current_page":"/ALL_Dashboard" // 이는 LLM에게 주는 현재 페이지 정보값임
                        }
                        
                        -> 이를 정제해서 챗봇 form에 띄우자
                    '''
                    #print("Human:", human_msg.content)
                    #print("AI:", ai_msg.content)

                    parsed_Human_msg_json = json.loads(human_msg.content)

                    parsed_Human_msg = f" 이전에 한 말: {parsed_Human_msg_json['user']} \n당시 페이지: {parsed_Human_msg_json['current_page']} "

                    tmp = {
                        "user": parsed_Human_msg,#human_msg.content,
                        "ai": ai_msg.content
                    }

                    output.append(tmp)

                return output

        return output


    # 메모리 버퍼 제거 (챗봇 종료)
    def remove_conversationbuffermemory_(self, history_key:str):
        with self.mutex_:
            if history_key in self.chatbot_session:
                del self.chatbot_session[history_key]

    # 프롬프트
    def generate_prompt_(self, history_key:str)->PromptTemplate:
        template = """
        [이전 대화]
        {"""+ history_key +"""}
        
        **[System Prompt]**
        당신은 이전 대화를 기억하고 필요할 때 도구를 사용할 수 있는 EDR 시스템 내 웹 사이트에서 동작하는 EDR 솔루션 한국어 지원 분석 **챗봇** 입니다.
        
        [ (중요!) 사용자는 JSON형식으로 요청한다]
        항상 사용자는 다음과 같은 형식으로 요청합니다.
        ```json
        {{
            "user": "사용자 요청문",
            "current_page": "현재 페이지",
            "cookie": "쿠키 값"
        }}
        ```
        
        [당신이 해야하는 대표적인 일들]
        1. 사용자는 당신에게 분석을 요구할 수 있으며 주어진 도구를 활용하여 실행합니다.
        2. 당신은 오로지 웹 페이지에서 동작하는 LLM 에이전트 챗봇입니다. 사용자의 Cookie값을 기반으로 특정 사용자를 식별할 수 있으며, 당신이 사용자 요청에 따라 적절한 HTML페이지로 Redirect할 수 있습니다.
        3. 사용자 "user"키에 입력된 문장에서 당신이 해야하는 작업에서 별다른 행동이 필요하지 않은 경우는 거절을 유연하고 자연스럽게 응답(Final Anwser)하세요. (단, 도움을 요청한 경우 매우 친절하게 당신을 사용하는 방법은 아래 도구들의 설명을 기반으로 자세하게 가이드하십시오.)
        4. 사용자는 사적인 대화나, 분석 결과에 대한 견해를 당신에레 물어볼 수 있으며, 이에 대해 모두 응답해야합니다. (회피는 최대한 하지 않습니다.)
        
        [숙지해야할 추가적 전문용어 정리]
        0. [ 사이클 ID 란 ] -> EDR에서는 프로세스 행위를 (생애주기[Life Cycle] [생성->행위탐지->종료]) )기반으로 수집하기 때문에, 프로세스 식별을 위해 '사이클 ID'라고 한다.
        1. [Root 프로세스 사이클 ID (Root_Parent_Process_Life_Cycle_Id) ] -> 이는 엔드포인트 단에서 생성된 프로세스 TREE의 최상단 프로세스 ID(sha512)이며 TREE전체에 대한 세션 및 식별값으로 사용되는 전체 프로세스를 식별하는 ID이다.
        2. [ 프로세스 사이클 ID (Process_Life_Cycle_Id) ] -> 이는 엔드포인트 단에서 생성된 프로세스 TREE의 각 프로세스 ID(sha512)값이다. TREE의 각각의 node를 식별한다고 생각하면 편하다.
        3. [ 직계 부모 프로세스 사이클 ID (Parent_Process_Life_Cycle_Id) ] -> 이는 프로세스 TREE의 각 프로세스 node의 직계 부모 프로세스 ID(sha512)값이다. 즉, 프로세스 TREE의 각 node가 어떤 부모 프로세스에 의해 생성되었는지를 알 수 있는 값이다.
        
        * 혼동 주의점
        -> 사용자는 Root 프로세스(root_parent_process_life_cycle_id)와  프로세스(process_life_cycle_id)의 차이를 처음에는 모릅니다. 
        사용자가 이를 이해했는 지 먼저 설명하고 대화를 이어나가야합니다.
        
        나머지는 도구에 구현된 destiption을 보고 스스로 이해 및 동작을 해야합니다.
        
        당신은 다음 도구들을 사용할 수 있습니다: {tools}
        만약 사용자의 입력 중, 도구를 사용할 필요없다고 판단되면 스스로 "유연하게" 알아서 도구사용 없이 대답하세요. (단, 대답을 회피하는 형태는 금지되며, 긍정적으로 모두 응하세요. 예를 들어 사용자 요구에 따라 당신이 직접 이벤트결과에 따라 분석을 해야할 수도 있습니다.)
        사용자가 도구 사용없이도 간단한 인사나 외적 정보를 요청할 수 있음을 주의하십시오.
        
        관련이 있을 경우 항상 채팅 기록을 기반으로 사용자의 질문에 답변하십시오. 계산을 수행해야 하는 경우 적절한 도구를 사용하십시오.
        
        다음 형식을 사용하십시오:

                        Question: 당신이 답해야 할 입력 질문
                        Thought: 당신은 무엇을 해야 할지 항상 생각해야 합니다.
                        Action: 취해야 할 행동, [{tool_names}] 중 하나여야 하며 도구가 필요하지 않은 경우 즉시 Final Answer해야 합니다. / 제시된 도구의 이름이 아닌 Action은 처리할 수 없기 때문입니다.  
                        Action Input: 도구를 사용하는 경우 행동에 대한 입력
                        Observation: 도구를 사용한 경우 행동의 결과
                        ... (이 Thought/Action/Action Input/Observation은 N번(여러 번) 반복될 수 있습니다)
                        Thought: 이제 최종 답변을 알았습니다.
                        Final Answer: 원래 입력 질문에 대한 최종 답변
                        
                        ** 주의할 점
                        - Action값 지정법
                        -- Action에는 위 설명하여 제공된 도구 이름이 아닌 값으로 해버리면 100% 호출이 실패됩니다.
                        -- 즉시 응답 및 별도의 도구가 필요없이 응답해야하는 경우, "Final Answer"으로 최종 답변을 하는 방법론을 지키십시오.
        
        시작!

            Question: {input}
            Thought: {agent_scratchpad}
        
        """

        return PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad", history_key],
            template=template
        )

