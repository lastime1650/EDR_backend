#----

from typing import Optional, List, Any, Dict, Tuple, Union

from typing import Any

from langchain.agents import create_react_agent, AgentExecutor
from langchain.agents.output_parsers import ReActSingleInputOutputParser
from langchain.chains.question_answering.map_rerank_prompt import output_parser
from langchain.llms.ollama import Ollama # ollama LLM모델
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains.llm import LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackManager
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables.utils import Input
from langchain_core.tools import Tool

from _LLM_Server_.VectorStore.Intelligences.CAPEC.To_VectorStore import CAPEC_to_VectorStore
from _LLM_Server_.VectorStore.Intelligences.MITRE_ATTACK.To_VectorStore import MITRE_ATTACK_to_VectorStore
import json

#---
# AI 에이전트 커스텀 출력 파서
class _CustomOutputParser(ReActSingleInputOutputParser):
    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        if "Invalid Format: Missing 'Action:' after 'Thought:'" in text:
            print("🚫 Invalid Format 오류 감지: Action 누락. No Action 처리합니다.")
            # return AgentAction(tool="no_action", tool_input={}, log=text)
            return AgentFinish(return_values={"output":text}, log=text)

        try:
            return super().parse(text)
        except Exception as e:
            print(f"⚠️ 파싱 에러 발생 (기본 Parser): {e}. No Action 처리합니다.")
            #return AgentAction(tool="no_action", tool_input={}, log=text)
            #return super().parse(text)  # 무시하고
            if "직접 응답" in text or "is not a valid tool" in text:
                output_string = str(text.split("Thought:")[1]).split("Action")[0] if "Action" in text.split("Thought:")[1] else text.split("Thought:")[1]
                return AgentFinish(return_values={"output": output_string}, log=output_string)
            elif "Action: None" in text:
                return AgentFinish(return_values={"output": "EDR과 관련한 질문을 부탁드리겠습니다."}, log=text)
            else:
                return AgentFinish(return_values={"output": text}, log=text)

#---
# 이 모듈은 어떤 평가든 간에 "전반적인 LLMchain"을 생성하는 클래스를 구현한다.

class LLM_logic_Maker():
    def __init__(self, LLM_Model_obj:Any, Prompt_System_Message:str, ConversationID:str=None):
        self.Agent_Chain = None
        self.init_(ConversationID, LLM_Model_obj, Prompt_System_Message)
        return

    def init_(self,  LLM_Model_obj:Any, Prompt_System_Message:str, ConversationID:str=None):
        # 대화 메모리 생성
        conversation_memory_inst = None
        if (ConversationID):
            conversation_memory_inst = ConversationBufferMemory(
                memory_key=ConversationID,
                return_messages=True
            )

        Prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template('''
                        System: ''' + Prompt_System_Message + '''
                        Human say: {input}
                        AI:
                        '''),
                HumanMessagePromptTemplate.from_template("{input}"),
                MessagesPlaceholder(variable_name=ConversationID)
            ]
        )

        self.Chain = LLMChain(
            llm=LLM_Model_obj,
            prompt=Prompt,
            memory=conversation_memory_inst
        )

    # LLM 평가 모델이 생성(self._init())된 후 호출 가능
    def Query(self, Input:str)->str:
        # 체인 실행
        output = self.Chain.invoke({"input": Input})["text"]
        return output


from _LLM_Server_.llm_enum import LLM_req_Type

from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Share_converstaion_mem import Share_ConversationMemory
# 이미 Conversation이 있을 때 사용.
class LLM_logic_Maker_with_ConversationMemoryBuffer():
    def __init__(self, LLM_Model_obj:Any, Prompt:Any, Conversation_obj:Optional[ConversationBufferMemory]):

        #self.__init(LLM_Model_obj, Prompt, Conversation_obj)
        return

    def _normal_create_chain(self,  LLM_Model_obj:Any, Prompt:Any, Conversation_obj:Optional[ConversationBufferMemory]):


        self.LLM = LLMChain(
            llm=LLM_Model_obj,
            prompt=Prompt,
            memory=Conversation_obj # 대화 메모리 인스턴스
        )
        return
    def _agent_init(self, LLM_Model_obj:Any, Prompt:Any, Conversation_obj:Optional[ConversationBufferMemory], Agent_tools:List[Tool]):

        # 에이전트 생성
        agent = create_react_agent(
            llm=LLM_Model_obj,
            tools=Agent_tools,
            prompt=Prompt,
            output_parser=_CustomOutputParser()
        )

        # 실행기 생성
        self.LLM = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=Agent_tools,
            memory=Conversation_obj,
            verbose=True,
            handle_parsing_errors=True  # 파싱 에러 처리 추가
        )
        return

    # LLM 평가 모델이 생성(self._init())된 후 호출 가능
    def _Query(self, Input:str)->(bool, str):

        #try:
            # 체인 실행
        output = self.LLM.invoke({"input": Input})
        q = ""
        # 일반 LLM인 경우 "text" 키가 존재.
        # 에이전트 LLM인 경우 "output"키가 존재.
        # 둘다 틀린경우, 그대로 반환한다.

        if "text" in output:
            # 일반 LLM
            q = output["text"].replace("```json","")\
            .replace("```","")\
            .replace("\n","")
        elif "output" in output:
            # 에이전트 LLM
            q = output["output"].replace("```json","")\
            .replace("```","")\
            .replace("\n","")
        else:
            # 둘다 틀린경우, 그대로 반환한다.
            q = str(output)

        return True, q

# 평가 전용
class LLM_eval_start(LLM_logic_Maker_with_ConversationMemoryBuffer):
    def __init__(self, LLM_Eval_Type:LLM_req_Type ,LLM_Model_obj:Any, Prompt:Any, Conversation_ID:str, Conversation_manager_obj:Share_ConversationMemory):

        self.LLM_Eval_Type = LLM_Eval_Type

        self.ConversationID = Conversation_ID
        self.ConversationMemoryManager_inst = Conversation_manager_obj

        # EVAL 타입에 따라 대화 메모리 관리 여부 체크 후 메모리 오브젝트 가져오기
        # ** TYPE_EVAL은  메모리가 필요 없다.
        self.Conversation_obj:Optional[ConversationBufferMemory] = None
        if LLM_Eval_Type != LLM_Eval_Type.TYPE_EVAL:  # 유형 평가는 메모리가 필요 없다.

            if LLM_Eval_Type == LLM_Eval_Type.MIDDLE_EVAL or LLM_Eval_Type == LLM_Eval_Type.FINAL_EVAL: # 중간 평가와 최종 평가는 대화 메모리를 새로 구축한다.( 그 이후는 Query 메서드 참조 )
                New_Conversation_obj =  ConversationBufferMemory(memory_key=Conversation_ID, return_messages=True)
                self.Conversation_obj =  New_Conversation_obj

        super().__init__(LLM_Model_obj, Prompt, self.Conversation_obj)
        super()._normal_create_chain(LLM_Model_obj, Prompt, self.Conversation_obj)

    def Query(self, Input:str)->Tuple[bool, str]:
        result_bool, llm_said = super()._Query(Input)

        # 하위 코드는 후처리 코드이다.
        # 항상 새로운 평가결과를 HDD에 저장하는 작업이나 기존 HDD에 저장된 대화에 결과를 추가하는 등의 작업이 포함된다.

        # 중간 평가
        if self.LLM_Eval_Type == LLM_req_Type.MIDDLE_EVAL:
            self.ConversationMemoryManager_inst.Save_Conversation_from_buff(self.ConversationID, self.Conversation_obj) # 항상 새로운 평가결과를 HDD에 저장한다.

        # 최종 평가
        elif self.LLM_Eval_Type == LLM_req_Type.FINAL_EVAL:
            # 현 Final Eval에서 얻은 Conversation 메모리를 MIDDLE_EVAL한 memory에 Message를 추가한다(넣어줌)
            output_middle_eval_conversation_buff = self.ConversationMemoryManager_inst.Get_Conversation(ConversationID=self.ConversationID, is_from_hdd=True)
            if output_middle_eval_conversation_buff:
                output_middle_eval_conversation_buff.chat_memory.messages.extend( self.Conversation_obj.chat_memory.messages) # Middle_Eval 대화 버퍼에 Final Eval 결과를 추가한다.

                self.ConversationMemoryManager_inst.Save_Conversation_from_buff(self.ConversationID,output_middle_eval_conversation_buff) # 항상 새로운 평가결과를 HDD에 저장한다.

        return result_bool, llm_said

# 대화 전용
class LLM_Chat_start(LLM_logic_Maker_with_ConversationMemoryBuffer):
    def __init__(self, LLM_Model_obj:Any, Prompt:Any, Conversation_buff:ConversationBufferMemory):

        super().__init__(LLM_Model_obj, Prompt, Conversation_buff)
        super()._normal_create_chain( LLM_Model_obj, Prompt, Conversation_buff)

    def Query(self, Input:str)->Tuple[bool, str]:
        return super()._Query(Input)


# 에이전트 전용
class LLM_Agent_start(LLM_logic_Maker_with_ConversationMemoryBuffer):
    def __init__(self, LLM_Model_obj:Any, Prompt:Any, Conversation_buff:ConversationBufferMemory, Agent_tools:List[Tool]):

        super().__init__( LLM_Model_obj, Prompt, Conversation_buff)
        super()._agent_init(LLM_Model_obj, Prompt, Conversation_buff, Agent_tools)

    def Query(self, Input:str)->Tuple[bool, str]:
        return super()._Query(Input)