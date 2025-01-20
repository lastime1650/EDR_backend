import queue, threading
from typing import Optional, Any, List, Dict

from _Analysis_Server_.PROVIDER_ANALYSIS_SCRIPT.Provider_service import Provider_Analysis_service # 사용자가 직접 추가해야함


# FILE TYPE
def Start_File_Type_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
  #pint(f"Analysis -> {DATA}")
  output = {
      "default_network_type_Analysis_results": []
  }

  if "REMOTE_IP" not in DATA:
      #[1/2]실패
      output["default"] = "Can't analyze it"
      queue_instance.put(output)  # 완료
      return

  # URLhaus 분석
  URLhaus_result_queue =analysis_instance.URLhaus_Analysis(str( DATA["REMOTE_IP"] ))
  URLhaus_result = URLhaus_result_queue.get()
  #print(yara_result)


  # 분석 정보 추가. ( list )
  output["default_network_type_Analysis_results"].append(URLhaus_result) # 추가

  queue_instance.put(output) # 완료
  return





# init 시작
def Start_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=Start_File_Type_Analysis, args=(analysis_instance, queue_instance, DATA))
    thread.start()

    return queue_instance