import queue, threading

from _Analysis_Server_.PROVIDER_ANALYSIS_SCRIPT.Provider_service import Provider_Analysis_service # EDR기본제공 분석 모듈(무조건 사용)

# FILE TYPE
def Start_File_Type_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
    output = {
      "default_file_type_Analysis_results": [] # key는 마음대로 해도 됨 LLM이 알아서 판단
    }

    '''
        분석 진행
        
        단, queue에 꼭 어떤 결과든 간에 반환해줘야함
        
        이 Thread에서 반환하지 않으면 **지연 및 성능 저하**됩니다. 
        
    '''

    queue_instance.put(output) # 완료
    return



# init 시작
def Start_Analysis(analysis_instance: Provider_Analysis_service, queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=Start_File_Type_Analysis, args=(analysis_instance, queue_instance, DATA))
    thread.start()

    return queue_instance