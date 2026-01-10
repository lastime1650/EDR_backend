from typing import Optional, Dict, Any, List, Tuple, Union

from langchain.agents import create_react_agent, AgentExecutor
from langchain.chains.llm import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.memory import ConversationSummaryMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import Tool

from LLM.LLM_Cluster import LLM_Cluster
import json

        
class LLM_Manager:
    def __init__(self):
        # LLM 클러스터
        self.llm_cluster = LLM_Cluster()

    def Start_General_LLM_V1(
            self,
            input_json:dict,
            prompt: PromptTemplate,
            conversation_buffer: Optional[ ConversationBufferMemory ] = None
    )->str:

        model_name, model = self.llm_cluster.Get_Model()

        General_Chain = LLMChain(
            llm=model,
            prompt=prompt,
            memory=conversation_buffer,
           # verbose=True
        )
        
        if conversation_buffer:
            output = General_Chain.invoke({'input':json.dumps(input_json,ensure_ascii=False)})#({"input": conversation_id})
        else:
            output = General_Chain.invoke(json.dumps(input_json,ensure_ascii=False))#({"input": conversation_id})
        
        

        # 모델 반환
        self.llm_cluster.Release_Model(model_name)

        return output['text']
    
    
    # LLM 수동관리 필요
    def Start_General_LLM_V2(
            self,
            input_json:any,
            prompt: PromptTemplate,
            
            model:any,
            memory: ConversationSummaryMemory
    )-> Dict[str, Any]:

        # model_name, model = self.llm_cluster.Get_Model()
        
        General_Chain = LLMChain(
            llm=model,
            prompt=prompt,
            memory=memory,
           # verbose=True
        )
        
        output = General_Chain.invoke({'input':input_json})['text']

        # 모델 반환
        # self.llm_cluster.Release_Model(model_name)

        return output

    def Start_Agent_LLM(
            self,
            input_json:dict,
            tools:List[Tool],
            prompt: PromptTemplate,
            conversation_buffer: Optional[ ConversationBufferMemory ] = None
    )->Dict[str, Any]:

        model_name, model = self.llm_cluster.Get_Model()
        print(f"사용 모델 명:{model_name}")
        # 에이전트 생성
        agent = create_react_agent(
            llm=model,
            tools=tools,
            prompt=prompt,
            #output_parser=_CustomOutputParser()
        )

        # 실행기 생성
        agent_LLM = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=conversation_buffer,
            verbose=True,
            handle_parsing_errors=True  # 파싱 에러 처리 추가
        )

        output = agent_LLM.invoke(input_json)#({"input": conversation_id})

        # 모델 반환
        self.llm_cluster.Release_Model(model_name)

        return output
