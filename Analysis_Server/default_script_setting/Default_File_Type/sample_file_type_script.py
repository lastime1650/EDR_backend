import queue, threading
from typing import Optional, Any, List, Dict

from _Analysis_Server_.PROVIDER_ANALYSIS_SCRIPT.Provider_service import Provider_Analysis_service # 사용자가 직접 추가해야함


# FILE TYPE
def Start_File_Type_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
    #pint(f"Analysis -> {DATA}")
    output = {
      "default_file_type_Analysis_results": [] # key는 마음대로 해도 됨 LLM이 알아서 판단
    }
    #print(DATA)
    if not( "binary" in DATA):
      #[1/2]실패
      output["default"] = "Can't analyze it"
      queue_instance.put(output)  # 완료
      return

    # binary의 경우 무조건 BASE64 인코딩인지 확인해야한다.
    binary = analysis_instance.BASE64_to_Binary(str(DATA["binary"]))
    if not binary :
      # [2/2]실패
      output["default"] = "Can't analyze it"
      queue_instance.put(output)  # 완료
      return

    # 최종 검증 성공
    print(len(binary))
    ''' 
        Analyze_Processing,,,,,,,,!@! 
    '''
    #Yara 분석
    yara_result_queue =analysis_instance.Yara_Analysis(binary) # Yara는 비동기처리 지원하므로
    yara_result = yara_result_queue.get()
    #print(yara_result)


    # 분석 정보 추가. ( list )
    output["default_file_type_Analysis_results"].append(yara_result) # 추가

    queue_instance.put(output) # 완료
    return





# init 시작
def Start_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=Start_File_Type_Analysis, args=(analysis_instance, queue_instance, DATA))
    thread.start()

    return queue_instance