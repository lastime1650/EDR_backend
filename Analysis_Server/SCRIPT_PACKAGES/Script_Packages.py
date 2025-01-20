import enum
import inspect
import sys
import threading
import time
import types
import importlib.util
from typing import Optional, List
import queue

from _Analysis_Server_.PROVIDER_ANALYSIS_SCRIPT.Provider_service import Provider_Analysis_service

# 스크립ㅌ트 타입 ENUM값
class Script_Packages_type_enum(enum.Enum):
    file = 0
    network = 1
    registry = 2 # 지원 고민중

class Script_Packages:
    def __init__(self):
        self.scripts = {} # 사용자 정의 스크립트 리스트
        self.Provider_Analysis_service = Provider_Analysis_service() # EDR제공형 외부 분석 서비스

        self.remove_script_name_queue:List[str] = [] # 삭제 요청 대기 큐 (script 이름을 전달)
        self.remove_script_name_queue_mutex = threading.Lock()
        threading.Thread(target=self._check_remove_script_loop,daemon=True).start()

    def _check_remove_script_loop(self):
        while True:
            time.sleep(1)
            # 삭제 요청 대기 큐에 있는 경우 제거
            with self.remove_script_name_queue_mutex:
                if len(self.remove_script_name_queue) > 0:
                    for script_name in self.remove_script_name_queue:
                        if script_name in self.scripts:
                            self._remove_script(script_name)

    def Add_Script(self, script_name: str, script_type: Script_Packages_type_enum, python_code: str) -> bool :

        # 스크립트 중복 검사 ( 이름 필터 )
        if script_name in self.scripts:
            return False

        # 새로운 모듈을 생성합니다.
        module = types.ModuleType(script_name)

        # sys.modules에 모듈을 추가하여 import 가능
        sys.modules[script_name] = module

        # python_code가 실행될 떄 모든 모듈의 접근이 가능하도록 함.  ( 위험하긴 해 )
        for name, existing_module in sys.modules.items():
            if hasattr(existing_module, "__dict__"):
                module.__dict__[name] = existing_module

        # 문자열 스크립트를 모듈에서 실행합니다.
        exec(python_code, module.__dict__)

        # 최종 저장
        self.scripts[script_name] = {
            "module": module,
            "type": script_type.name,# 문자열로 저장
            "reference_count": 0 # 스크립트 해제시 사용되는 "참조 카운트" ref: Windows Kenrel 의 ObReferenceObject 로부터 따옴
        }

        return True

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

#-------------------------------------------------------------------------------------------------------------------------

    # type은 이미 정해진것.
    # script_names는 에이전트가 현재 사용가능한 이름이여하며, script_packages에 등록하고 있어야하는 정보.
    def Start_Analysis(self, script_type:Script_Packages_type_enum, blacklist_script_names:list=None, DATA:dict=None) -> Optional[dict] :

        if DATA == None:
            return None

        if blacklist_script_names == None:
            blacklist_script_names = []

        queue_list = []

        output = {
            "Analysis_Result": []
        }

        using_scripts = []  # 참조 해제 시 정확히 사용된 스크립트 목록

        for script_name in self.scripts:

            # 블랙리스트 스크립립트는 제외하고, 타입이 다른 스크립트는 제외한다.
            if script_name in blacklist_script_names or self.scripts[script_name]["type"] != script_type.name:
                continue

            # 참조 카운트 증가 (필수적)
            self.scripts[script_name]["reference_count"] += 1

            queue_instance = queue.Queue()

            queue_list.append( self.scripts[script_name]["module"].Start_Analysis(self.Provider_Analysis_service, queue_instance, DATA) )

            using_scripts.append(script_name)

        if len(queue_list) > 0:

            # 모두 완료할 때까지 대기
            for q in queue_list:
                output["Analysis_Result"].append( dict( q.get() ) )
            output["status"] = "success"
            output["message"] = "성공"

        else:
            output["Analysis_Result"] = []
            output["status"] = "fail"
            output["message"] = "스크립트 실행 중 오류 발생"

        # 참조 카운트 감소 (필수적)
        for script_name in using_scripts:
            self.scripts[script_name]["reference_count"] -= 1

        return output

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


# python_code 수정 (Script_Packages를 import하여 사용)
python_code = """
import queue
import threading
from _Analysis_Server_.PROVIDER_ANALYSIS_SCRIPT.scripts.YARA.YARA import Yara_Analyzer # 사용자가 직접 추가해야함

def custom(queue_instance:queue.Queue, DATA:bytes):

  
  queue_instance.put({"custom_res":DATA}) # 완료

  print( Yara_Analyzer().Start_Analysis(DATA).get() ) # Yara 요청
  
  return 

# 기본 구조
def Start_Analysis(queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=custom, args=(queue_instance, DATA))
    thread.start()
    
    return queue_instance

"""
# Script_Packages 인스턴스 생성
#script_packages = Script_Packages()



# 모듈 생성
#script_packages.Add_Script("my_module", Script_Packages_type_enum["file"], python_code)


#target = open(r"C:\Users\Administrator\Desktop\KDU\kdu.exe", 'rb').read()
#script_packages.Start_Analysis(Script_Packages_type_enum["file"], None, target)

