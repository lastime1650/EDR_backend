
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection # rule 모음

from typing import Union, Optional

import yaml

from EDR.servers.Elasticsearch import ElasticsearchAPI

from enum import Enum
class SigmaTargetEndpoint(Enum):
    windows = 1
    linux = 2
    macos = 3
    #...

class SigmaRuleType(Enum):
    process_creation = 1
    registry = 2
    image_load = 3
    file_system = 4
    network = 5

class SigmaStoredRule():
    def __init__(self, rule_dict:dict, rule_pySigma:SigmaRule, rule_elasticsearch_eql:list[str]):
        self.rule_dict = rule_dict
        self.rule_pySigma = rule_pySigma
        self.rule_elasticsearch_eql = rule_elasticsearch_eql

class SigmaOutputs():
    def __init__(self):
        self.SigmaResults:dict[list] = {}
    
    def Add(self, eql_output:list, rule_dict:dict, rule_name:str):
        
        
        if rule_name not in self.SigmaResults:
            self.SigmaResults[rule_name] = []
        
        
        self.SigmaResults[rule_name].append(
            {
                "detected_event": eql_output,
                "rule": rule_dict
            }  
        )
        
    def Output(self, rule_name:Optional[SigmaRuleType]=None)->Optional[list]:
        try:
            if rule_name == None:
                return self.SigmaResults
            else:
                return self.SigmaResults[rule_name]
        except:
            return None
        
        

class Sigma_Manager():
    def __init__(self, 
                 es: ElasticsearchAPI, # rule 매칭
                 Root_Directory:str="/docker__WEBserver/BehaviorAnalyzerManagement/SigmaManagement/sigma_all_rules/rules" # /docker__WEBserver -> dockerfile 절대경로
                 ):
        self.es = es 
        self.Root_Directory = Root_Directory
        
        # field_mapping은 sigma->eql 각 쿼리값과 SIEM-EDR-* 인덱스 필드와 매핑을 정의합니다.
        self.SigmaRuleFieldMapping = {
            SigmaRuleType.process_creation.name: {
                
                #1.  **`Image`**:
                #    *   실행된 프로세스의 실행 파일 경로 (예: `C:\Windows\System32\cmd.exe`)
                #    *   가장 흔하게 사용되는 필드 중 하나입니다.
                #
                "Image": "unique.process_behavior_events.Process_Created.ImagePath",
                #2.  **`CommandLine`**:
                #    *   실행된 프로세스의 전체 명령줄 (실행 파일 경로 + 인자) (예: `cmd.exe /c echo hello > file.txt`)
                #    *   매우 중요하며, 다양한 공격 기법을 탐지하는 데 활용됩니다.
                #
                "CommandLine": "unique.process_behavior_events.Process_Created.CommandLine",
                #3.  **`ParentImage`**:
                #    *   해당 프로세스를 실행시킨 부모 프로세스의 실행 파일 경로.
                #    *   프로세스 관계를 파악하고 비정상적인 부모-자식 관계를 탐지하는 데 사용됩니다.
                #
                "ParentImage": "unique.process_behavior_events.Process_Created.Parent_ImagePath",
                #4.  **`ParentCommandLine`**: X
                #    *   부모 프로세스의 전체 명령줄.
                #    *   `ParentImage`와 유사하게 부모 프로세스의 상세 정보를 확인하는 데 사용됩니다.
                #
                #5.  **`User`**: X
                #    *   프로세스를 실행한 사용자 계정.
                #    *   특정 사용자의 활동을 추적하거나 권한 상승 등을 탐지하는 데 사용됩니다.
                #
                #6.  **`Hashes`**:
                #    *   실행 파일의 해시값 (MD5, SHA1, SHA256 등).
                #    *   알려진 악성 파일의 해시를 탐지하는 데 사용됩니다. Sigma 룰에서는 보통 특정 해시 타입과 함께 사용됩니다 (예: `hashes|contains: 'SHA1=...'`).   
                #
                "Hashes": "unique.process_behavior_events.Process_Created.ProcessSHA256",
                #9.  **`OriginalFileName`**:
                #     *   실행 파일의 원래 파일 이름 (패킹되거나 이름이 변경된 경우에도 원래 이름 정보를 포함할 수 있습니다).
                #
                #10. **`Description`**:
                #    *   실행 파일의 파일 설명 메타데이터.
                #
                #11. **`CurrentDirectory`**:
                #    *   프로세스가 실행될 때의 현재 작업 디렉토리.
                #
                #12. **`IntegrityLevel`**:
                #    *   프로세스의 무결성 수준 (Low, Medium, High, System 등). 권한 상승 시도 등을 탐지하는 데 사용됩니다.
                
            },
            SigmaRuleType.registry.name:{
                "Image": "unique.process_behavior_events.Process_Created.ImagePath",
                
                "TargetObject": "unique.process_behavior_events.registry.RegistryObjectName",
                "EventType": "unique.process_behavior_events.registry.RegistryKey",
            },
            SigmaRuleType.file_system.name: {
                "Image": "unique.process_behavior_events.Process_Created.ImagePath",
                
                "TargetFilename": "unique.process_behavior_events.file_system.FilePath",
            },
            SigmaRuleType.image_load.name: {
                "Image": "unique.process_behavior_events.Process_Created.ImagePath",

                "ImageLoaded" : "unique.process_behavior_events.image_load.ImagePath",
            },
            SigmaRuleType.network.name: {
                "Image": "unique.process_behavior_events.Process_Created.ImagePath",
                
                "DestinationHostname": "unique.process_behavior_events.network.geoip.As",
            }
        }
        
        self.SigmaRules = {
            "windows": {
                SigmaRuleType.process_creation.name: {
                    "rules" : list[SigmaStoredRule]( self.load_sigma_rules______(Root_Directory+"/windows/process_creation", rule_type=SigmaRuleType.process_creation) ),
                },
                SigmaRuleType.registry.name:{
                    "rules" : list[SigmaStoredRule]( self.load_sigma_rules______(Root_Directory+"/windows/registry", rule_type=SigmaRuleType.registry) ),
                },
                SigmaRuleType.image_load.name:{
                    "rules" : list[SigmaStoredRule]( self.load_sigma_rules______(Root_Directory+"/windows/image_load", rule_type=SigmaRuleType.image_load) ),
                },
                SigmaRuleType.file_system.name:{
                    "rules" : list[SigmaStoredRule]( self.load_sigma_rules______(Root_Directory+"/windows/file", rule_type=SigmaRuleType.file_system) ),
                }
            }
        }
        
        
    
    # 지원가능한 Rule 모두 수행
    def Sigma_Analysis(
        
        self, 
        target:SigmaTargetEndpoint, 
        
        agent_id:str, root_process_id:str, process_id:str
        
        )->SigmaOutputs:
        
        
        OutPut = SigmaOutputs()
        
        # 호환 가능한 엔드포인트의 sigma rule 가져와 반복
        for SigmaRule_info_key_name in self.SigmaRules[target.name]:
            
            # 실제 규칙 가져옴
            loaded_rules: list[SigmaStoredRule] = self.SigmaRules[target.name][SigmaRule_info_key_name]["rules"]
            
            print(SigmaRule_info_key_name)

            for rule_info in loaded_rules:
                
                for EQL_query in rule_info.rule_elasticsearch_eql:
                    
                    if len(EQL_query) == 0:
                        continue
                    
                    EQL_query = EQL_query.replace("\\", "\\\\") # 문자열 출력시 \\ 으로 나오게 하기 위해 \\\\ 으로 변환하여 eql 쿼리 구문 문제 없도록한다.
                    
                    eql_output = self.eql_query(
                        eql=EQL_query,
                        
                        agent_id=agent_id,#'d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf',
                        root_process_id=root_process_id,#'a7ad5a9b121d726053c7d99414135afd6efb654a90008a0cf436a4a43613d2e442a20c539a5673f44fe2f132e5bf0cdd6cfd4c081682f519b0478e893689af80',
                        process_id=process_id,
                    )
                    if eql_output == None:
                        continue
                    
                    # eql 결과 저장
                    OutPut.Add(
                        eql_output=eql_output,
                        rule_dict=rule_info.rule_dict,
                        
                        rule_name=SigmaRule_info_key_name
                    )
                    #print(f"일치! --> {OutPut.Output()}")
                    print(f"일치! --> {rule_info.rule_dict}")
        
        
        return OutPut
    
    
    
    # 내부 함수
    # Elasticsearch 쿼리
    def eql_query(self, eql:str, agent_id:str, root_process_id:str,process_id:str )->Optional[list[dict]]:
        
        try:
            return self.es.EQL_Query(
                eql_query=eql,
                
                dsl_filter=self.make__DSL_filter_(agent_id=agent_id, root_process_id=root_process_id, process_id=process_id),
                
                index="siem-edr-*"
            )
        except:
            # 예외 발생하는 경우는?
            # 1. 시그마 eql 이 Elasticsearch 필드에 포함되지 않은 경우.
            
            return None # eql 쿼리 문제인경우 시그마 판단이 불가능함
    
    # 기본 쿼리문
    # 쿼리 생성
    def make__DSL_filter_(self, agent_id:str, root_process_id:str,process_id:str )->dict:
        return {
            "bool":{
                "filter": [
                    {
                        "term": {
                            "categorical.Agent_Id": agent_id # 에이전트 ID
                        }
                    },
                    {
                        "term": {
                            "categorical.process_info.Root_Parent_Process_Life_Cycle_Id": root_process_id  # 최상위 루트 프로세스 사이클 아이디
                        }
                    },
                    {
                        "term": {
                            "categorical.process_info.Process_Life_Cycle_Id": process_id  # 프로세스 사이클 아이디
                        }
                    }
                ]
            }
        }
    
    # sigma rule files -> dictionary ( JSON ) 변환 작업
    def load_sigma_rules______(self, rule_root_dir:str, rule_type:SigmaRuleType)->list[SigmaStoredRule]:
        
        # Yaml 경로 추출
        from Utility.FileManager import File_Manager
        
        output:list[SigmaStoredRule] = []
        for rule_file_path in File_Manager(rule_root_dir).Searching_Files("yml"):
            
            
            
            from sigma.collection import SigmaCollection
            from sigma.backends.elasticsearch import EqlBackend
            
            
            ruleSigma = SigmaCollection.from_yaml(
                open(rule_file_path, encoding="utf-8").read()
            )
            
            try:
                
                # EQL 작업
                
                # 1. EQL 추출 
                EQL_ruleSigma:list[str] = EqlBackend().convert(ruleSigma) # EQL query
                
                # 2. EQL field 매핑 작업 ( 인자 가져와서 어떤 규칙인가에 따라 필드매핑 진행 )
                for i, eql in enumerate(EQL_ruleSigma):
                    
                    for key in self.SigmaRuleFieldMapping[rule_type.name]:
                        eql = eql.replace(key, self.SigmaRuleFieldMapping[rule_type.name][key])
                        
                        
                    EQL_ruleSigma[i] = eql # 테스트 성공
                
                
                
                rule_dict = yaml.load(open(rule_file_path, encoding="utf-8"), Loader=yaml.FullLoader) # Sigma Yaml to Dict
                pySigma_instance = SigmaRule.from_dict(rule_dict) # pySigma object 

                
                if 'custom1.yml' in rule_file_path:
                    print(EQL_ruleSigma)
                    print(rule_dict)
                
                
                
                output.append(
                    
                    
                    SigmaStoredRule(
                        rule_dict=rule_dict,
                        rule_pySigma=pySigma_instance,
                        rule_elasticsearch_eql=EQL_ruleSigma
                    )
                    
                    
                )
                
            except:
                continue
        
        print(f"Sigma Loaded ->>> {rule_type.name} -")
        return output


#test_url = r"BehaviorAnalyzerManagement/SigmaManagement/sigma_all_rules/rules"
#Sigma_Manager(test_url)