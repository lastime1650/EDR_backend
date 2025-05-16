import queue, threading
from typing import Optional, Any, List, Dict


from Tool_Management.ToolManager import ToolManager # 사용자가 직접 추가해야함


# NETWORK TYPE
def Start_Network_Type_Analysis(analysis_service_instance: ToolManager, queue_instance:queue.Queue, DATA:dict):
    
    remoteip = ""
    try:
        remoteip = str(DATA["remoteip"])
    except:
        queue_instance.put(None)

    
    output = {
      "default": {}
    }
    
    # 분석 수행
    analyzed_results = {
        "analyzed_results_": {}
    }
    
    # VirusTotal -> 아직 구현 X 
    
    
    # URLhaus
    URLhaus_Analysis_Result = analysis_service_instance.URLhaus_Analysis(analysis_target_IP=remoteip).get()
    if URLhaus_Analysis_Result:
        analyzed_results["analyzed_results_"]["urlhaus"] = {
            "description": "URLhaus 조회",
            "result": URLhaus_Analysis_Result,
            "status": True  # 분석 결과 여부
        }
        print(analyzed_results["analyzed_results_"]["urlhaus"])
        
    
    
    if len(analyzed_results["analyzed_results_"]) > 0:
        Return(
            queue_instance=queue_instance,
            analyzed_result=analyzed_results
        )
    else:
        queue_instance.put(None)
    

# 반환
def Return(queue_instance:queue.Queue, analyzed_result:dict):
    #print(f"analyzed_result -> {analyzed_result}")
    queue_instance.put(analyzed_result)
    return

# init 시작
# Input 필수 구현 메서드
def Start_Analysis(analysis_service_instance: ToolManager, queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=Start_Network_Type_Analysis, args=(analysis_service_instance, queue_instance, DATA))
    thread.start()

    return queue_instance