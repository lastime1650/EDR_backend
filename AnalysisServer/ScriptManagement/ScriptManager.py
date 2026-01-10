import base64
import enum
import hashlib
import sys
import threading
import time
import types
from typing import Optional, List
import queue


# Tool매니저
from Tool_Management.ToolManager import ToolManager

# enum 
from ScriptManagement.globalenum import Script_Packages_type_enum # script

# 분석 결과 엘라스틱 저장 모듈 
from ScriptManagement.elasticsearch_.save_to_elasticsearch import Analysis_ElasticSearch

class ScriptManager:
    def __init__(self, elasticsearch_host:str, elasticsearch_port:int):
        
       
        self.analysis_mutex = threading.Lock()
        
        
        self.scripts = {}
        self.scripts_mutex = threading.Lock()
        
        self.ToolManager = ToolManager()
        
        self.Analysis_ElasticSearch = Analysis_ElasticSearch(
            elastichost=elasticsearch_host,
            elasticport=elasticsearch_port,
        )
        
        self.remove_script_name_queue:List[str] = [] # 삭제 요청 대기 큐 (script 이름을 전달)
        self.remove_script_name_queue_mutex = threading.Lock()
        threading.Thread(target=self._check_remove_script_loop,daemon=True).start()
    
    # 스크립트 추가
    def Add_Script(self, script_name: str, script_type: Script_Packages_type_enum, python_code: str) -> bool :
    
        # 스크립트 중복 검사 ( 이름 필터 )
        if script_name in self.scripts:
            return False

        # 새로운 모듈을 생성합니다.
        module = types.ModuleType(script_name)

        # sys.modules에 모듈을 추가하여 import 가능
        sys.modules[script_name] = module

        # python_code가 실행될 떄 모든 모듈의 접근이 가능하도록 함. 
        for name, existing_module in sys.modules.items():
            if hasattr(existing_module, "__dict__"):
                module.__dict__[name] = existing_module

        # 문자열 스크립트를 모듈에서 실행합니다.
        exec(python_code, module.__dict__)

        # 최종 저장
        self.scripts[script_name] = {
            "module": module,
            "type": script_type.name,# 문자열로 저장
            "reference_count": 0, # 스크립트 해제시 사용되는 "참조 카운트" ref: Windows Kenrel 의 ObReferenceObject 로부터 따옴
            "code": python_code
        }

        return True
    
    # 현 등록한 스크립트 조회
    def Get_script(self, script_type:Script_Packages_type_enum = None, with_script_name:str = None)->Optional[dict]:
        if not script_type and not with_script_name:
            return None
        if with_script_name and not script_type:
            if with_script_name in self.scripts:
                output = {
                    "module": self.scripts[with_script_name]["module"].__name__,
                    "type": self.scripts[with_script_name]["type"]
                }
                return output
            else:
                return None
        elif script_type and not with_script_name:
            output = {}
            for script_name_v in self.scripts:
                if self.scripts[script_name_v]["type"] == script_type.name:
                    output = {
                        "module": self.scripts[script_name_v]["module"].__name__,
                        "type": self.scripts[script_name_v]["type"]
                    }
            return output
        else:
            # 모두 존재하는 경우,
            for script_name_v in self.scripts:
                if self.scripts[script_name_v]["type"] == script_type.name and self.scripts[script_name_v]["module"].__name__ == with_script_name:
                    return {
                        "module": self.scripts[script_name_v]["module"].__name__,
                        "type": self.scripts[script_name_v]["type"]
                    }
            return None
    def Get_all_scripts(self)->List[dict]:
        output = []
        for script_name_v in self.scripts:
            output.append(
                {
                    "module": self.scripts[script_name_v]["module"].__name__,
                    "type": self.scripts[script_name_v]["type"],
                    "code": self.scripts[script_name_v]["code"]
                }
            )
        return output
    
    # 스크립트 삭제 처리 루프 스레드
    def _check_remove_script_loop(self):
        while True:
            time.sleep(1)
            # 삭제 요청 대기 큐에 있는 경우 제거
            with self.remove_script_name_queue_mutex:
                if len(self.remove_script_name_queue) > 0:
                    for script_name in self.remove_script_name_queue:
                        if script_name in self.scripts:
                            self._remove_script(script_name)
    
    # 삭제 요청 대기 큐 추가(외부 호출용)
    def Remove_script(self,script_name:str):
        if script_name in self.scripts:
            # 이미 큐에 있는 경우 False
            if script_name in self.remove_script_name_queue:
                return False
            else:
                # 이미 참조 카운트가 0 이고, 삭제 대기 큐에 있는 경우 제거
                if self.scripts[script_name]["reference_count"] == 0:
                    self._remove_script(script_name)
                    return True
                else:
                    # 바로 불가능하면 큐에 등록 (지연)
                    self.remove_script_name_queue.append(script_name)
                    return True

    # 실제 삭제 로직(외부 호출 금지)
    def _remove_script(self, script_name:str):
        del self.scripts[script_name] # 해당 인스턴스의 dict로부터 삭제
        del sys.modules[script_name] # sys dict로부터 삭제
        print(f"삭제된 스크립트 -> {script_name}")
        return
    
    ##########################
    
    def Start_Analysis(self, script_type:Script_Packages_type_enum, DATA  ) :
        
        
        with self.analysis_mutex :
            # 멀티 스레드 처리
            
            # 분석 완료 확인
            if self.Get_Analysis_Result_(script_type=script_type, DATA=DATA):
                # 이미 분석 완료된 경우 skip
                return
            
            if DATA == None:
                return

            queue_list:list[queue.Queue] = []

            using_scripts = []  # 참조 해제 시 정확히 사용된 스크립트 목록
            print(f"스크립트 분석 시작!")
            with self.scripts_mutex:
                for script_name in self.scripts:

                    # 블랙리스트 스크립립트는 제외하고, 타입이 다른 스크립트는 제외한다.
                    if self.scripts[script_name]["type"] != script_type.name:
                        continue
                    
                    queue_instance = queue.Queue()

                    queue_list.append( self.scripts[script_name]["module"].Start_Analysis(self.ToolManager, queue_instance, DATA) ) # 분석 유형 일치한 스크립트 실행

                    using_scripts.append(script_name)
                    
                    # 참조 카운트 증가 (필수적)
                    self.scripts[script_name]["reference_count"] += 1

            if len(queue_list) > 0:

                # 모두 완료할 때까지 대기
                result:list[dict] = []
                for q in queue_list:
                    
                    try:
                        data = q.get() 
                        
                        if not data:
                            continue
                        elif isinstance(data, Exception):
                            continue
                        elif isinstance(data, dict):
                            result.append( data )
                    except:
                        continue

                
                if len(result) > 0:

                    # 분석 결과 가져오기 성공

                    # ElasticSearch에 저장 ( mutex 필요 )
                    # 단일 처리 전송.
                    print("ELK에 전달합니다...")
                    with self.Analysis_ElasticSearch.mutex_:
                        self.save_to_elasticsearch(
                            SCRIPT_TYPE=script_type,
                            DATA=DATA,
                            analyzed_results=result
                        )

            # 참조 카운트 감소 (필수적)
            with self.scripts_mutex:
                for script_name in using_scripts:
                    self.scripts[script_name]["reference_count"] -= 1
            
    
    def save_to_elasticsearch(
        self,
        SCRIPT_TYPE:Script_Packages_type_enum, # 분석 타입
        DATA:dict, # 분석 타입에 따른 동적 데이터
        analyzed_results:List[dict] # 분석 결과 데이터
    ):
        if SCRIPT_TYPE == Script_Packages_type_enum.file:

            # 사용자 쿼리 JSON -> SHA256 추출
            SHA256 = ""
            if "sha256" in DATA and len(DATA["sha256"]) > 0:
                SHA256 = str(DATA["sha256"]).lower()
            else:
                if "binary" in DATA:
                    SHA256 = hashlib.sha256(  base64.b64decode(DATA["binary"]) ).hexdigest()
                else:
                    raise Exception("분석 데이터에 sha256가 없습니다.")

            # 사용자 쿼리 JSON -> 파일 사이즈 추출
            if "file_size" in DATA:
                FILE_SIZE = DATA["file_size"]
            else:
                FILE_SIZE = len(base64.b64decode(DATA["binary"]))

            self.Analysis_ElasticSearch.Add_FILE_(
                sha256=SHA256,
                file_size=FILE_SIZE,
                extra=analyzed_results # 각 모듈별 저장된 결과들
            )
        elif SCRIPT_TYPE == Script_Packages_type_enum.network:
            REMOTE_IP = ""
            if "remoteip" in DATA and len(DATA["remoteip"]) > 0:
                REMOTE_IP = str(DATA["remoteip"]).lower()
            else:
                raise Exception("분석 데이터에 remoteip가 없습니다.")

            self.Analysis_ElasticSearch.Add_NETWORK_(
                remoteip=REMOTE_IP,
                extra=analyzed_results
            )
        else:
            raise Exception("알 수 없는 분석 타입입니다.")
        
    # 분석 결과 조회 ( elasticsearch로 조회한다 )
    def Get_Analysis_Result_(self, script_type:str,  DATA:dict)->Optional[bool]:

        if script_type == Script_Packages_type_enum.file.name:
            
            sha256 = ""
            
            if "sha256" in DATA:
                sha256 = str(DATA["sha256"]).lower()
            elif "binary" in DATA:
                sha256 = hashlib.sha256(  base64.b64decode(DATA["binary"]) ).hexdigest()
            else:
                raise Exception("분석 데이터에 sha256값이 없습니다.")

            # 엘라스틱서치 를 통해 sha256 조회
            return self.Analysis_ElasticSearch.is_document_exist_from_FILE(
                sha256=sha256
            )

        elif script_type == Script_Packages_type_enum.network.name:
            network_remoteip = str(DATA["remote_ip"]).lower()
            
            return self.Analysis_ElasticSearch.is_document_exist_from_NETWORK(
                remoteip=network_remoteip
            )

        else:
            return None