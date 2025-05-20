
from sigma.rule import SigmaRule
from sigma.collection import SigmaCollection # rule 모음

from typing import Union, Optional

import yaml

from EDR.servers.Elasticsearch import ElasticsearchAPI

from enum import Enum
class SigmaTargetEnum(Enum):
    windows = 1
    linux = 2
    macos = 3
    #...

class SigmaRuleType(Enum):
    process_creation = 1

class SigmaStoredRule():
    def __init__(self, rule_dict:dict, rule_pySigma:SigmaRule, rule_elasticsearch_eql:list[str]):
        self.rule_dict = rule_dict
        self.rule_pySigma = rule_pySigma
        self.rule_elasticsearch_eql = rule_elasticsearch_eql

class Sigma_Manager():
    def __init__(self, 
                 es: ElasticsearchAPI, # rule 매칭
                 Root_Directory:str="/docker__WEBserver/BehaviorAnalyzerManagement/SigmaManagement/sigma_all_rules/rules" # /docker__WEBserver -> dockerfile 절대경로
                 ):
        self.es = es 
        self.Root_Directory = Root_Directory
        
        # field_mapping은 sigma->eql 각 쿼리값과 SIEM-EDR-* 인덱스 필드와 매핑을 정의합니다.
        self.SigmaRuleFieldMapping = {
            "process_creation": {
                    
                #1.  **`Image`**:
                #    *   실행된 프로세스의 실행 파일 경로 (예: `C:\Windows\System32\cmd.exe`)
                #    *   가장 흔하게 사용되는 필드 중 하나입니다.
                #
                "Image": "categorical.Process_Created.ImagePath",
                #2.  **`CommandLine`**:
                #    *   실행된 프로세스의 전체 명령줄 (실행 파일 경로 + 인자) (예: `cmd.exe /c echo hello > file.txt`)
                #    *   매우 중요하며, 다양한 공격 기법을 탐지하는 데 활용됩니다.
                #
                "CommandLine": "categorical.Process_Created.CommandLine",
                #3.  **`ParentImage`**:
                #    *   해당 프로세스를 실행시킨 부모 프로세스의 실행 파일 경로.
                #    *   프로세스 관계를 파악하고 비정상적인 부모-자식 관계를 탐지하는 데 사용됩니다.
                #
                "ParentImage": "categorical.Process_Created.Parent_ImagePath",
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
                "Hashes": "categorical.Process_Created.ProcessSHA256",
                #7.  **`ProcessId`**:
                #    *   해당 프로세스의 고유 ID (PID).
                #    *   탐지 조건 자체보다는 이벤트 간 상관관계 분석 등에 더 활용될 수 있습니다.
                #
                "ProcessId" : "categorical.Process_Created.ProcessId",
                #8.  **`ParentProcessId`**:
                #    *   부모 프로세스의 PID.
                #
                "ParentProcessId" : "categorical.Process_Created.Parent_ProcessId",
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
                
            }
        }
        
        self.SigmaRules = {
            "windows": {
                "process_creation": {
                    "rules" : list[SigmaStoredRule]( self.load_sigma_rules______(Root_Directory+"/windows/process_creation", rule_type=SigmaRuleType.process_creation) ),
                }
            }
        }
        
        
    
    # 공통 행위
    def Process_Creation(
        
        self, 
        target:SigmaTargetEnum, 
        
        agent_id:str, root_process_id:str, 
        self_process_Image:str, self_process_CommandLine:str, parent_process_Image:str
        
        )->list[dict]:
        loaded_rules:list[SigmaStoredRule] = self.SigmaRules[target.name]["process_creation"]["rules"]
        
        for rule_info in loaded_rules:
            
            for EQL_query in rule_info.rule_elasticsearch_eqls:
            
                if len(EQL_query) == 0:
                    continue
                
                # EQL_query 와 index template 필드 매핑이 이루어져야한다.
                
                Elasticsearch_query = self.es.make_eql_query__(
                    eql = EQL_query,
                    agent_id=agent_id,
                    root_process_id=root_process_id
                )
                print(Elasticsearch_query)
                quit()
        
        pass
        
    def Network_Connection(self, target:SigmaTargetEnum, hostname:str):
        pass
    def FileSystem(self, target:SigmaTargetEnum, file_path:str, action:str):
        pass
    
    # 운영체제 별도 행위
    def Registry(self, registry_function:str, registry_key:str): # Windows특화
        pass
    def Load_Image(self, Image:str): # Windows특화
        pass
    
    
    # Sigma 결과 Dict
    # 아마 규칙 내용 자체를 output하거나 2개이상 [] 으로 반환가능할 듯 
    
    
    
    # 내부 함수
    
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

                
                
                output.append(
                    
                    
                    SigmaStoredRule(
                        rule_dict=rule_dict,
                        rule_pySigma=pySigma_instance,
                        rule_elasticsearch_eql=EQL_ruleSigma
                    )
                    
                    
                )
                
            except:
                continue
            
        return output


#test_url = r"BehaviorAnalyzerManagement/SigmaManagement/sigma_all_rules/rules"
#Sigma_Manager(test_url)