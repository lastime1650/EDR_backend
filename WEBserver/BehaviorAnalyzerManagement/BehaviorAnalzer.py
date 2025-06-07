from typing import Optional


from EDR.EDRManager import EDR_Manager
from BehaviorAnalyzerManagement.SigmaManagement.Sigma_Manager import Sigma_Manager, SigmaTargetEndpoint, SigmaOutputs

# LLM
from LLM.LLMManager import LLM_Manager
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationSummaryMemory
from langchain.memory import ConversationBufferMemory
import threading
from queue import Queue
# Sigma rule 로 행위 분석 패턴 사용할 것 ( Mitre attack 과 연계 가능 )

import json

from enum import Enum
class LLM_Analysis_Type(Enum):
    process = 1 # 프로세스 연관 분석
    tree = 2 # 트리 연관 분석


from BehaviorAnalyzerManagement.Behavior_Elasticsearch import Behavior_ElasticSearch

class BehaviorAnalyzer():
    def __init__(self, Sigma_Manager:Sigma_Manager, EDR_Manager:EDR_Manager, LLM_Manager:LLM_Manager, behavior_elasticsearch:Behavior_ElasticSearch):
        self.Sigma_Manager = Sigma_Manager  # Sigma_Manager 인스턴스
        self.EDR_Manager = EDR_Manager  # ElasticsearchAPI 인스턴스
        self.LLM_Manager = LLM_Manager # LLM_Manager 인스턴스
        
        
        
        self.behavior_elasticsearch = behavior_elasticsearch # LLM 분석 결과 저장 관리 인스턴스
        
        
        # 싱글 스레드 연관 분석 처리
        self.loop_tree_analysis_mutex__ = threading.Lock()
        self.tree_analysis_queue = Queue()
        threading.Thread(
            target=self.loop_tree_analysis
        ).start()
    

    # 자동 연관 분석 트리거 (Beta) Root 프로세스 Tree 생성 후 제한시간 (1hours) 후 분석 진행
    # 싱글 스레드 처리
    def loop_tree_analysis(self):
        
        while True:
            requested:dict = self.tree_analysis_queue.get()
            print("loop_tree_analysis 실행")
            
            agent_id = requested["agent_id"]
            root_process_id = requested["root_process_id"]
            
            # 분석 요청 
            self.Start_Behavior_Analyzer(
                endpoint_type=SigmaTargetEndpoint.windows,# Windows 
                agent_id=agent_id,
                root_process_id=root_process_id
            )
            print("loop_tree_analysis 완료")
            
    def Thread_Tree_Analysis_Queue(self, agent_id:str, root_process_id:str):
        self.tree_analysis_queue.put(
            {
                "agent_id": agent_id,
                "root_process_id": root_process_id
            }
        )
            
    
    def Start_Behavior_Analyzer(self,  endpoint_type: SigmaTargetEndpoint, agent_id:str, root_process_id:str):
        
        # Tree -> LLM 연관 분석 -> elasticSearch 저장
        self.start_tree_analysis______(endpoint_type, agent_id=agent_id, root_process_id=root_process_id)
        return
    
    
    # 내장 메서드
    def is_already_analyzed_by_process_cycle_id(self, agent_id:str, root_process_id:str)->Optional[list[dict]]:
        output  = self.EDR_Manager.ElasticsearchAPI.Query(
            query={
                "query" : {
                    "bool":{
                        "filter":[
                            {
                                "term":{
                                    "categorical.Agent_Id": agent_id
                                }
                            },
                            {
                                "term":{
                                    "categorical.process_info.Root_Parent_Process_Life_Cycle_Id": root_process_id
                                }
                            },
                            {
                                "exists":{
                                    "field":"unique.process_behavior_events.Process_Created"
                                }
                            }
                        ]
                    }
                },
                "size":1,
                "_source":{
                    "includes":[
                        "unique.process_behavior_events.Process_Created.ProcessSHA256",
                        "unique.process_behavior_events.Process_Created.Parent_ProcessSHA256"
                        #"categorical.Agent_Id",
                        #"categorical.process_info.Root_Parent_Process_Life_Cycle_Id"
                    ]
                }
                
            },
            index="siem-edr-*",
            is_aggs=False
        )
        if len(output) > 0:
            Self_SHA256 = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["ProcessSHA256"]
            Parent_SHA256 = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["Parent_ProcessSHA256"]
            Root_Parent_SHA256 = Parent_SHA256
            return self.behavior_elasticsearch.get_by_sha256(process_sha256=Self_SHA256, parent_sha256=Parent_SHA256)
        else:
            return None
    
    def is_already_analyzed_(self,agent_id:str, root_process_id:str, tree_node_depth:int, tree_node_count:int)->Optional[dict]:
        output  = self.EDR_Manager.ElasticsearchAPI.Query(
            query={
                "query" : {
                    "bool":{
                        "filter":[
                            {
                                "term":{
                                    "categorical.Agent_Id": agent_id
                                }
                            },
                            {
                                "term":{
                                    "categorical.process_info.Root_Parent_Process_Life_Cycle_Id": root_process_id
                                }
                            },
                            {
                                "exists":{
                                    "field":"unique.process_behavior_events.Process_Created"
                                }
                            }
                        ]
                    }
                },
                "size":1,
                "_source":{
                    "includes":[
                        "unique.process_behavior_events.Process_Created.ProcessSHA256",
                        "unique.process_behavior_events.Process_Created.Parent_ProcessSHA256"
                        #"categorical.Agent_Id",
                        #"categorical.process_info.Root_Parent_Process_Life_Cycle_Id"
                    ]
                }
                
            },
            index="siem-edr-*",
            is_aggs=False
        )
        if len(output) > 0:
            
            Self_SHA256 = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["ProcessSHA256"]
            Parent_SHA256 = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["Parent_ProcessSHA256"]
            Root_Parent_SHA256 = Parent_SHA256
            
            # LLM index에서 찾기
            #agent_id = output[0]["_source"]["categorical"]["Agent_Id"]
            #root_process_id = output[0]["_source"]["categorical"]["process_info"]["Root_Parent_Process_Life_Cycle_Id"]
            
            llm_result = self.behavior_elasticsearch.get_by_tree(Self_SHA256, Parent_SHA256, Root_Parent_SHA256, tree_node_depth, tree_node_count)
            if llm_result:
                
                return llm_result
            else:
                return None
        else:
            return None
        
        
    # 기본 프로세스 Tree 가져오기
    def start_tree_analysis______(self, endpoint_type: SigmaTargetEndpoint, agent_id:str, root_process_id:str)->Optional[dict]:
        
        # 사전 Tree 구하기
        Tree = self.EDR_Manager.Get_Process_Tree(
            root_process_id=root_process_id,
            need_analysis_results=False 
            )[0]
        if not Tree:
            return None
        
        # Tree 깊이와 개수
        tree_node_depth:int = Tree["_node_depth"]["key"]
        tree_node_count:int = Tree["_node_count"]["key"]

        # 사전 분석 결과 확인 -> 이미 이전에 완성된 TREE 분석결과가 있었는지
        LLM_RESULT = self.is_already_analyzed_(agent_id, root_process_id, tree_node_depth, tree_node_count)
        if LLM_RESULT:
            return LLM_RESULT
        
        # 이벤트 원본 + 정적 분석 결과 가져오기
        Tree = self.EDR_Manager.Get_Process_Tree(
            root_process_id=root_process_id,
            need_analysis_results=True # 분석 결과 결합 
            )[0]
        if not Tree:
            return None
        
        return self.Tree_analysis______(
            
            endpoint_type,
            Tree, 
            
            tree_node_depth,
            tree_node_count,
            
            ) # 분석 + 시그마 결합한 최종 Tree 반환
    
    # Tree 이벤트에 분석결과 결합   
    def Tree_analysis______(self, endpoint_type: SigmaTargetEndpoint,Tree:dict, tree_node_depth:int, tree_node_count:int)->dict:
        print("TREE 연관분석 시작")
        current:dict = Tree["self"]
        Self__SHA256 = current["process_event"]["process_info"]["Process_Created"]["ProcessSHA256"]
        Self__SHA256_filesize:int = int( current["process_event"]["process_info"]["Process_Created"]["ImageSize"] )
        
        Parent__SHA256 = current["process_event"]["process_info"]["Process_Created"]["Parent_ProcessSHA256"]
        Root_Parent__SHA256 = Parent__SHA256
        
        #########################################################################################
        
        Process_LLM_result_Tree = {
            "self": {},
            "child": []
        }
        
        # LLM 연관 분석 # 
        LLM_RESULT = self.LLM_check(current)
        
        Process_LLM_result_Tree['self'] = LLM_RESULT # Process LLM 연관분석 결과 저장
        
        self.Tree_recursive____________(endpoint_type, Tree["child"], Process_LLM_result_Tree["child"])

        
        #
        #
        #
        # 여기부터는 Tree 분석까지 완료된 상태
        #
        #
        
        
        LLM_RESULT = self.LLM_Analysis_tree(Process_LLM_result_Tree, tree_node_depth, tree_node_count)
        
        # - LLM의 결과 LLM_RESULT에서 node_depth, node_count 정보를 스스로 응답(Elasticsearch에 저장됨)하게 하여 증명하도록 한다.
        
        # << tree >
        self.behavior_elasticsearch.Add_EDR_Analysis(
            llm_result=LLM_RESULT,
            self_sha256=Self__SHA256,
            parent_sha256=Parent__SHA256,
            root_parent_sha256=Root_Parent__SHA256,
            self_filesize=Self__SHA256_filesize
        )
        
        print("TREE 연관분석 최종완료")
        
        return LLM_RESULT
    
    # 재귀함수
    def Tree_recursive____________(self, endpoint_type: SigmaTargetEndpoint, Child:list[dict], Process_LLM_result_Child:list):
        if len(Child) == 0:
            return None
        else:
            for event_dict in Child:
                        
                Process_LLM_result_Tree = {
                    "self": {},
                    "child": []
                }
                
                current:dict = event_dict["self"]
                
                # LLM 연관 분석 # 
                LLM_RESULT = self.LLM_check(current)
                
                
                Process_LLM_result_Tree['self'] = LLM_RESULT # Process LLM 연관분석 결과 저장
                
                
                # Child LLM 분석 결과 추가
                Process_LLM_result_Child.append(
                    Process_LLM_result_Tree
                )
                
                self.Tree_recursive____________(endpoint_type, event_dict["child"], Process_LLM_result_Tree["child"]) # 다음 프로세스(자식) 이동



    def LLM_check(self, self_event:dict)->Optional[dict]:
        if len(self_event) == 0:
            return None
        
        process_event:dict = self_event["process_event"]
        agent_id:str = process_event['endpoint_info']['Agent_Id']
        root_process_id:str = process_event['process_info']['Root_Parent_Process_Life_Cycle_Id']
        process_id:str = process_event['process_info']['Process_Life_Cycle_Id']
        
        behavior_timeline:list[dict] = self_event["behavior_timeline_sorted"] #behavior_timeline
        
        return self.LLM_Analysis_process(
            events=behavior_timeline,
            detected_sigma_rule=self.Sigma_Manager.Sigma_Analysis(
                                                        target=SigmaTargetEndpoint.windows,
                                                        agent_id=agent_id,
                                                        root_process_id=root_process_id,
                                                        process_id=process_id
                                                    )
        )
    ###############
    # LLM #
    ###############
    
    # [ 1/2 TREE]
    def LLM_Analysis_tree(self, events:dict, tree_node_depth:int, tree_node_count:int)->dict:
        
        
        memory = ConversationBufferMemory(memory_key="test", return_messages=True)
        
        while True:
            
            o = self.LLM_Manager.Start_General_LLM_V1(
                    input_json=events,
                    prompt=self.get_Prompt(analysis_type=LLM_Analysis_Type.tree, history_key="test"),
                    conversation_buffer = memory
                )
            print(f"tree 연관분석 결과 --> {o}")
            JSON = json.loads(
                    ( o.replace("```json", "").replace("```", "").replace("\n", "") )
                )
            
            if JSON["tree_node_depth"] != tree_node_depth and JSON["tree_node_count"] != tree_node_count:
                events = {
                    "problem": f"당신의 tree_node_depth 값과 tree_node_count값은 서로 다릅니다. 실제 원본 Tree의 count값은 {tree_node_count}이며, depth는 {tree_node_depth}입니다. 다시 확인하고 JSON 분석결과내세요."
                }
                continue
            elif JSON["tree_node_depth"] != tree_node_depth:
                events = {
                    "problem": f"당신의 tree_node_depth 값은 서로 다릅니다. 실제 원본 Tree의 depth는 {tree_node_depth}입니다. 다시 확인하고 JSON 분석결과내세요"
                }
                continue
            elif JSON["tree_node_count"] != tree_node_count:
                events = {
                    "problem": f"당신의 tree_node_count 값은 서로 다릅니다. 실제 원본 Tree의 count값은 {tree_node_count}입니다. 다시 확인하고 JSON 분석결과내세요."
                }
                continue
            else:
                return JSON
        
        
    # [ 2/2 PROCESS]
    def LLM_Analysis_process(self, events:list[dict], detected_sigma_rule:list = [])->dict:
        history_key = "EDR_SIEM"
        
        
        
        model_name, model = self.LLM_Manager.llm_cluster.Get_Model()
        conversation_buffer = ConversationSummaryMemory(
                llm=model,
                memory_key=history_key,
                return_messages=True 
            )
        
        # Chunk별 제공
        currnet_chunk = 0 
        for i in range(0, len(events), 1500):
            
            currnet_chunk += 1500
            
            if currnet_chunk > len(events):
                currnet_chunk = len(events)
                self.LLM_Manager.Start_General_LLM_V2(
                    
                    input_json=events[i:currnet_chunk],
                    
                    prompt=self.get_Prompt(LLM_Analysis_Type.process,history_key),
                    model=model,
                    memory=conversation_buffer,
                )
                break
            else:
                self.LLM_Manager.Start_General_LLM_V2(
                    
                    input_json=events[i:currnet_chunk],
                    
                    prompt=self.get_Prompt(LLM_Analysis_Type.process,history_key),
                    model=model,
                    memory=conversation_buffer,
                )
        
        result:dict = {}
        input_query = self.LLM_INPUT_Process(detected_sigma_rule)
        while True:
            
            o = self.LLM_Manager.Start_General_LLM_V2(
                    
                input_json= input_query, # 최종 보고서 요구 멘트
                
                prompt=self.get_Prompt(LLM_Analysis_Type.process,history_key),
                model=model,
                memory=conversation_buffer,
            ).replace("```json", "").replace("```", "")
            
            try:
                result = json.loads(o)
                print(o)
                break
            except:
                
                input_query = self.LLM_INPUT_Process(detected_sigma_rule)
                input_query += '\n 이전 응답은 JSON 형식이 아닙니다. 다시 JSON으로 정확히 반환해주세요. '
                
                continue
        
        
        self.LLM_Manager.llm_cluster.Release_Model(model_name)
        return result
    
    # LLM 프롬프트
    def get_Prompt(self, analysis_type:LLM_Analysis_Type, history_key:str=None)->PromptTemplate:
        
        # PROCESS
        if analysis_type == LLM_Analysis_Type.process:
            return PromptTemplate(
                template='''
                이전 대화: {'''+history_key+'''}
                
                --
                
                EDR_SIEM_EVENTS: {input}
                
                --
                
                # System Prompt 시작 #
                role/mission(임무) -> 당신은 Endpoint Detection and Response (EDR)의 SIEM로그로부터 수집된 프로세스의 여러 이벤트를 행위 분석해야합니다. 또한 ConversationMemorybuffer를 통해 이전 기억이 가능하므로 심층있는 이벤트 맥락 이해를 할 수 있습니다.
                
                Point -> 프로세스의 행위 이벤트를 가지고 상관분석을 하는 것.
                Attention -> '악성 여부' 검증은 하지 않는다.( 단지, 프로세스 행위를 잘 풀이하는 것이 중요. )
                
                Provide -> 이벤트 행위 분석시 참고할 사항들은 제공된 SIEM 프로세스 이벤트에 해당하는 포함된 Analysis_Result인 정적분석 결과를 적극적 인용(가중치)하여 상관분석할 수 있다.(할루시네이션 방지)
                
                * Extra Infos
                1. 이벤트는 List[Dict]형식으로 제공되며, List의 요소 순서는 이벤트 발생 순 (Old->New)이다. "타임라인"상관분석이 중요하다.
                2. 이벤트 분석은 2번 이상 이어서 진행될 수 있다. 
                3. IP 주소의 경우 analysis 분석결과가 없으면 악성으로 판단하지 마시오. 
                4. 정확한 분석 결과 (analysis 관련 필드)가 없으면 즉시 악성으로 판단하지 않고, 행위 요약을 중점으로 하십시오. False Postive를 줄여야합니다.
                5. 상기 항목 4번의 목적달성을 위해 "불충분한 근거"로 인한 악성으로 판단하지 마십시오.
                6. Sigma Rule 이 발견된 경우, 처음에는 악성으로 판단하지말고, Rule의 행위 설명(Desciption)에 있는 정보를 확인하여 행위를 판단하고, 의심스러우 경우, 태그와 결합하십시오.
                # System Prompt 끝 #
                
                이제 상기 지침에 따라 분석하세요.
                ''',
                input_variables=['input', history_key],
            )
            
        # TREE
        elif analysis_type == LLM_Analysis_Type.tree:
            return PromptTemplate(
                template='''
                이전 대화: {'''+history_key+'''}
                
                --
                
                EDR_TREE_LLM_ANALYZED(json): {input}
                
                --
                
                # System Prompt 시작 #
                role/mission(임무) -> 당신은 Endpoint Detection and Response (EDR)의 각 프로세스 별 연관 분석 결과를 토대로 json형태의 tree구조로 생성된 'EDR_TREE_LLM_ANALYZED' 이벤트에 최종 분석해야합니다. 또한 ConversationMemorybuffer를 통해 이전 기억이 가능하므로 심층있는 이벤트 맥락 이해를 할 수 있습니다.
                
                Point -> 프로세스 TREE 행위 이벤트를 가지고 총 상관분석을 하는 것.
                Attention -> '악성 여부' 검증한다.( 단지, 프로세스 행위를 잘 풀이하는 것이 중요. )
                
                * Extra Infos
                1. 이벤트는 List[Dict]형식으로 제공되며, List의 요소 순서는 이벤트 발생 순 (Old->New)이다. "타임라인"상관분석이 중요하다.
                2. 이벤트 분석은 2번 이상 이어서 진행될 수 있다. 
                # System Prompt 끝 #
                
                이제 상기 지침에 따라 아래 JSON형태로  나타내어 분석 결과 제공하세요.
                * 각 'self' 필드는 한 프로세스의 연관 분석을 json을 의미합니다. 그리고 'child'는 해당 'self'의 자식 프로세스 결과를 의미합니다. 이 관계를 정확히 이해한 후 상관분석하세요.
                ```json
                {{
                    "tree_node_count":"이는 당신이 트리 구조를 이해하는 지 파악하기 위함입니다. int형으로 전체 트리에서 프로세스 노드 개수(self필드)를 정수 작성하세요.",
                    "tree_node_depth":"이는 당신이 트리 구조를 이해하는 지 파악하기 위함입니다. int형으로 전체 트리에서 프로세스 노드 깊이(self필드)를 정수 작성하세요. '깊이'의 의미는 'child가 생성된 횟수를 의미'하며, 노드의 개수를 의미하지 않습니다.",
                    "tree_summary": "Tree 전체 분석 결과에 대한 종합적인 개요를 작성",
                    "tree_detail": "Tree 전체 분석 결과에 대해 상세하고 디테일한 분석 결과를 나타냄",
                    "tree_relation": "Tree 전체 분석 결과를 기반으로 연관 분석 결과를 나타냄",
                    "tree_opinion": "이를 분석한 분석가의 '의견'을 나타냄",
                    "tree_anomaly": "이상탐지 결과를 위한 필드이며, Normal(정상행위) 인지 Abnormal(악성행위) 중 하나만 작성하세요.",
                    "tree_anomaly_score": "이상탐지 결과를 0.0~1.0 사이의 실수로 작성하세요.",
                    "tree_severity": "심각도 단어를 선정하여 나타내세요. low, medium, high, critical 중 하나",
                    "tree_tags": "List[str] 형식의 리스트 타입으로 이 연관 이벤트와 관련한 기술 유형 태그들을 작성하세요 (단순한 태그는 작성하지마세요.)",
                    "tree_suspicion_score": "분석자가 판단한 의심 수준을 0.0~1.0 사이 실수로 작성",
                    "tree_security": "해당 tree 전체 분석 후, 보호조치가 필요한 경우 지침을 작성하세요."
                }}
                ```
                
                * 모호한 답변은 하지마세요. 혼동을 야기합니다. 정확히 "~해야합니다"등 명확하고 실용적이며 실질적인 멘트를 작성하세요.
                * False Positive 문제가 없게하기 위해 "불충분한 근거"로 인한 악성으로 판단(Abnormal)하지 마십시오.
                * 추가적 조사가 필요한 경우가 위협으로 이어지는 경우에는 의심스러울 수 있지만, 그것이 아닌 경우는 악성으로 판단하지 마십시오.
                * 당신이 Abnormal/악성 으로 판단하려면 연관분석 흐름을 기반으로 충분히 근거를 제시해야만 허용됩니다.( 추가적인 분석이 필요하다는 것은 충분한 근거가 아닙니다. )
                ''',
                input_variables=['input', history_key],
            )
    
    # LLM -> process -> Input 작성시
    def LLM_INPUT_Process(self, Detected_Sigma_Rule:list = [])->str:
        
        return f"""
            
            Sigma Rule 조회결과 -> {Detected_Sigma_Rule}
            * Sigma Rule은 Mitre Attack 공격전술과 관련하여, 행위 탐지시 적극 참조하세요.
            * 조회되지 않은 경우 공란입니다. …
            
            자, 이제 EDR SIEM 이벤트는 모두 전달되었습니다. 당신이 지금껏 분석한 기억을 통하여 다음 총 보고서를 JSON형식으로 작성해주세요. 
            * 당신의 보고서 결과는 EDR 자동화 분석에 활용됩니다.
            * 모든 멘트는 AI처럼 작성하지 말고, 실제 전문가 처럼 핵심만 자세히 작성하세요.
            ```json
            {{
                "summary": "해당 이벤트에 대한 종합적인 개요를 작성",
                "detail": "상세하고 디테일한 분석 결과를 나타냄",
                "relation": "연관 분석 결과를 나타냄",
                "opinion": "당신의 의견을 자유롭게 작성하세요.",
                
                "correlation_score": "이 이벤트가 다른 이벤트들과 얼마나 강하게 연관되어 있는지를 0.0~1.0 사이 실수로 작성하세요.",
                "suspicion_score": "분석자가 판단한 의심 수준을 0.0~1.0 사이 실수로 작성하세요.",
                "evidence_weight": "행위 연관성의 강도 또는 증거의 확실성을 0.0~1.0 사이 실수로 표현하세요.",
                "trigger_probability": "해당 이벤트가 이후 악성 행위를 유발했을 확률을 0.0~1.0 사이 실수로 작성하세요.",
                "temporal_correlation": "시간적 연관성 강도를 0.0~1.0 사이 실수로 작성하세요.", (중요)
                 
                "anomaly": "이상탐지 결과를 위한 필드이며, Normal(정상행위) 인지 Abnormal(악성행위) 중 하나만 작성하세요.", (중요)
                "anomaly_score": "이상탐지 결과를 0.0~1.0 사이의 실수로 작성하세요.", (중요)
                "severity": "심각도 단어를 선정하여 나타내세요. low, medium, high, critical 중 하나 선택.",
                "tags": "List[str] 형식의 리스트 타입으로 이 연관 이벤트와 관련한 기술 유형 태그들을 작성하세요 (단순한 태그는 작성하지마세요.)"
            }}
            ```
            * 프로세스 연관 분석 지침
            1. IP 주소의 경우 analysis 분석결과가 없으면 악성으로 판단하지 마시오. 
            2. 정확한 분석 결과 (analysis 관련 필드)가 없으면 즉시 악성으로 판단하지 않고, 행위 요약을 중점으로 하십시오. False Postive를 줄여야합니다.
            3. 상기 항목 2번의 목적달성을 위해 "불충분한 근거"로 인한 악성으로 판단하지 마십시오.
        """