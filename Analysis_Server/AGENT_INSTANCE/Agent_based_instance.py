import json
import threading
import time
from typing import Optional, List

from _Analysis_Server_.SCRIPT_PACKAGES.Script_Packages import Script_Packages, Script_Packages_type_enum

class Agent_instance_manager():
    def __init__(self, Script_Packages_manager:Script_Packages):
        self.Agent_infos = {
            "agents": {}
        }
        self.Script_Packages_manager = Script_Packages_manager # 스크립트 패키지들

        # 삭제 큐 무한 루프
        self.remove_queue:List[str] = []
        self.remove_queue_mutex = threading.Lock()
        threading.Thread(target=self._check_remove_agent_loop,daemon=True).start()

    def _check_remove_agent_loop(self):
        while True:
            time.sleep(1)
            # 참조 카운트가 0 이고, 삭제 대기 큐에 있는 경우 제거
            with self.remove_queue_mutex:
                if len(self.remove_queue) > 0:
                    for agent_id in self.remove_queue:
                        if self.Agent_infos["agents"][agent_id]["reference_count"] == 0:
                            self._remove_Agent(agent_id)

    def Add_Agent(self, Agent_ID:str):

        # 중복 검사
        if Agent_ID in self.Agent_infos["agents"]:
            return False

        self.Agent_infos["agents"][Agent_ID] = \
            {
                "Blacklist_scripts": {
                    "file": [], # 파일 분석 type일 떄의 블랙리스트 스크립트 이름 리스트
                    "network": [], # 네트워크 type일 떄의 블랙리스트 스크립트 이름 리스트
                    "registry": [] # 레지스트리 type일 떄의 블랙리스트 스크립트 이름 리스트
                },
                "reference_count": 0, # 참조 카운트
            }

        if not Agent_ID in self.Agent_infos["agents"]:
            return False
        else:
            return True

    def Remove_Agent(self, Agent_ID:str):
        if not Agent_ID in self.Agent_infos["agents"]:
            return False # 등록안된 것을 지우려고 했으므로 False
        else:
            if Agent_ID in self.remove_queue:
                return False # 이미 지우고 있음
            else:
                #  바로 삭제 가능한지 검토
                if self.Agent_infos["agents"][Agent_ID]["reference_count"] == 0:
                    self._remove_Agent(Agent_ID)
                    return True
                else:
                    # 바로 불가능하면 큐에 등록 (지연)
                    self.remove_queue.append(Agent_ID)
                    return True

    def _remove_Agent(self, Agent_ID:str):
        del self.Agent_infos["agents"][Agent_ID]
        return

    def Set_BLACKLIST_script_to_Agent(self, Agent_ID:str, script_name:str, script_type:Script_Packages_type_enum):
        if script_type.name == "file":
            self.Agent_infos["agents"][Agent_ID]["Blacklist_scripts"]["file"].append(script_name)
        elif script_type.name == "network":
            self.Agent_infos["agents"][Agent_ID]["Blacklist_scripts"]["network"].append(script_name)
        else:
            return False

        return True

    def Get_script(self, script_type:Script_Packages_type_enum, script_name:str = None)->Optional[dict]:
        return self.Script_Packages_manager.Get_script(script_type, script_name)

    def Request_Analysis(self,  Agent_ID:str, Script_type:str, DATA:dict) -> Optional[dict]:

        if not Agent_ID in self.Agent_infos["agents"]:
            return {"status":"fail", "message":"에이전트가 등록되지 않았습니다."} # 에이전트 등록 검사

        # 참조 증가
        self.Agent_infos["agents"][Agent_ID]["reference_count"] += 1

        result = self.Script_Packages_manager.Start_Analysis(
            script_type=Script_Packages_type_enum[Script_type],
            blacklist_script_names=[],#list(self.Agent_infos["agents"][Agent_ID]["Blacklist_scripts"][Script_type.name]),
            DATA=DATA
        )

        # 참조 감소
        self.Agent_infos["agents"][Agent_ID]["reference_count"] -= 1

        return result



'''agent_mng = Agent_instance_manager( Script_Packages() )
agent_mng.Add_Agent("ABC")
print(agent_mng.Get_script(Script_Packages_type_enum["file"], "my_custom"))

# 스크립트 추가하기
python_code_for_a_sample = """
import queue
import threading

def custom(queue_instance:queue.Queue, DATA:bytes):
  #print(f"Analysis -> {DATA}")
  
  queue_instance.put({"custom_res":DATA}) # 완료
  return 

# 기본 구조
def Start_Analysis(queue_instance:queue.Queue, DATA:bytes):
    thread = threading.Thread(target=custom, args=(queue_instance, DATA))
    thread.start()
    
    return queue_instance

"""
agent_mng.Script_Packages_manager.Add_Script("my_custom", Script_Packages_type_enum["file"], python_code_for_a_sample)
print(agent_mng.Get_script(Script_Packages_type_enum["file"], ))
print( agent_mng.Request_Analysis("ABC", Script_Packages_type_enum["file"], b"Hello" ) )'''