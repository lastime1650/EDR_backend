from typing import Optional


from EDR.EDRManager import EDR_Manager
from BehaviorAnalyzerManagement.SigmaManagement.Sigma_Manager import Sigma_Manager, SigmaTargetEnum

# Sigma rule 로 행위 분석 패턴 사용할 것 ( Mitre attack 과 연계 가능 )

class BehaviorAnalzer():
    def __init__(self, Sigma_Manager:Sigma_Manager, EDR_Manager:EDR_Manager):
        self.Sigma_Manager = Sigma_Manager  # Sigma_Manager 인스턴스
        self.EDR_Manager = EDR_Manager  # ElasticsearchAPI 인스턴스
    
    def Start_Behavior_Analyzer(self,  endpoint_type: SigmaTargetEnum, agent_id:str, root_process_id:str):
        
        # Tree 구하기
        Tree = self.Get_Root_Process_Tree______(endpoint_type, agent_id=agent_id, root_process_id=root_process_id)
        if not Tree:
            return None
        
        # LLM 프로세스 연관 분석 진행 (self당 LLM 분석) -> 내부 메서드에서 진행하도록 구현하라
        
        # LLM 프로세스간 연관 분석 진행 (전체 LLM 분석)
        
        pass
    
    
    # 내장 메서드
    
    # 기본 프로세스 Tree 가져오기
    def Get_Root_Process_Tree______(self, endpoint_type: SigmaTargetEnum, agent_id:str, root_process_id:str)->Optional[dict]:
        Tree = self.EDR_Manager.Get_Process_Tree(root_process_id=root_process_id)[0]
        if not Tree:
            return None
        
        return self.Tree_with_Sigma______(endpoint_type, Tree, agent_id=agent_id, root_process_id=root_process_id) # 분석 + 시그마 결합한 최종 Tree 반환
    
    # Tree -> 이벤트 결합
    def Tree_with_Sigma______(self, endpoint_type: SigmaTargetEnum,Tree:dict, agent_id:str, root_process_id:str)->dict:
        
        current:dict = Tree["self"]
        self.Tree_with_Sigma_recursive____________(endpoint_type, agent_id, root_process_id, Tree["child"])

        return Tree
        
    # 재귀함수
    def Tree_with_Sigma_recursive____________(self, endpoint_type: SigmaTargetEnum, agent_id:str, root_process_id:str, Child:list[dict]):
        if len(Child) == 0:
            return None
        else:
            for event_dict in Child:
                current:dict = event_dict["self"] # 여기에 추가
                
                timeline_events = event_dict["self"]["behavior_timeline"]
                
                merged_events:list[dict] = []
                for event in timeline_events:
                    merged = self.Merge_Analysis_into_Event(endpoint_type, event, event["event_name"], agent_id, root_process_id)
                    
                    merged_events.append(
                        merged
                    )
                    
                event_dict["self"]["behavior_timeline"] = merged_events # Update
                
                self.Tree_with_Sigma_recursive____________(endpoint_type, agent_id, root_process_id, event_dict["child"]) # 다음 프로세스(자식) 이동
    
    # 이벤트 -> 분석 결과 결합
    def Merge_Analysis_into_Event(self, endpoint_type: SigmaTargetEnum, event:dict, event_name:str, agent_id:str, root_process_id:str) -> dict:
        output = {}
        
        if event_name == "Process_Created":
            
        
            
            self.Sigma_Manager.Process_Creation(
                
                endpoint_type,
                
                agent_id=agent_id,
                root_process_id=root_process_id,
                
                self_process_Image=dict(event).get("ImagePath", ""),
                self_process_CommandLine=dict(event).get("CommandLine", ""),
                parent_process_Image=dict(event).get("Parent_ImagePath", ""),

            )
            
        
        return output
        
        
        
        
        return output
        