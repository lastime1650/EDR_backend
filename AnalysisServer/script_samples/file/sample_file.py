import base64
import queue, threading
from typing import Optional, Any, List, Dict

from Tool_Management.ToolManager import ToolManager # 사용자가 직접 추가해야함


# FILE TYPE
def Start_File_Type_Analysis(analysis_service_instance: ToolManager, queue_instance:queue.Queue, DATA:dict):

    '''
    - 파일 바이너리가 요구된다.
    DATA {

        "binary" key가 요구된다.(base64)
    }
    '''

    output = {
      "default": {}
    }
    #print(DATA)
    if not( "binary" in DATA):
      #[1/2]실패
      output["failed_reason"] = "[File] 분석 시점 당시, 바이너리가 없어 정밀 분석 불가"
      print("바이너리 없음!")
      queue_instance.put(None)  # 완료
      return

    # binary의 경우 무조건 BASE64 인코딩인지 확인해야한다.
    binary = analysis_service_instance.BASE64_to_Binary(str(DATA["binary"]))
    if not binary :
      # [2/2]실패
      print("바이너리 없음!")
      output["failed_reason"] = "[File] 분석 시점 당시, 바이너리가 없어 정밀 분석 불가"
      queue_instance.put(None)  # 완료
      return

    # 최종 검증 성공
    #print(len(binary))
    ''' 
        Analyze_Processing,,,,,,,,!@! 
    '''

    VirusTotal_API_KEY = "b081a247f8bde7d98337dec2a44b9dff7d1eba19bd99a20c04395cea831177ee"
    SHA256 = analysis_service_instance.Binary_to_SHA256(binary)
    #FILE_SIZE = analysis_service_instance.Binary_to_Size(binary)

    # 분석 수행
    analyzed_results = {
        "analyzed_results_": {}
    }


    # 1. 바이러스토탈
    VirusTotal_Analysis_Result = analysis_service_instance.VirusTotal_Analysis( # 실패 가능 API문제
                        VirusTotal_API_KEY=VirusTotal_API_KEY,
                        File_Binary=binary
                    ).get()
    if VirusTotal_Analysis_Result:
        analyzed_results["analyzed_results_"]["virustotal"] = {
            "description": "바이러스토탈 결과 조회",
            "result": VirusTotal_Analysis_Result,
            "status": True  # 분석 결과 여부
        }
        #print(analyzed_results["analyzed_results_"]["virustotal"])
    #else:
    #    analyzed_results["analyzed_results_"]["virustotal"] = {
    #        "description": "바이러스토탈 결과 조회",
    #        "result": None,
    #        "status": False  # 분석 결과 여부
    #    }
    #print("Sigcheck_Analysis_Result 분석된")

    # 2. sigcheck ( Windows 전용 )
    Sigcheck_Analysis_Result:Optional[bool] = analysis_service_instance.Sigcheck_Analysis(analysis_target_bin=binary)
    if Sigcheck_Analysis_Result:
        analyzed_results["analyzed_results_"]["sigcheck"] = {
            "description": "EXE 실행 프로그램 인증서 여부 확인",
            "result": Sigcheck_Analysis_Result,
            "status": True  # 분석 결과 여부
        }
        #print(analyzed_results["analyzed_results_"]["sigcheck"])

    #print("Sigcheck_Analysis_Result 분석된")

    # 3. malwarebazaar
    MalwareBazaar_Analysis_Result = analysis_service_instance.MalwareBazaar_Analysis( # 실패 가능 (해시 없는 경우)
                        File_HASH256=SHA256
                    ).get()
    if MalwareBazaar_Analysis_Result:
        analyzed_results["analyzed_results_"]["malwarebazaar"] = {
            "description": "악성코드 DB 체크용 조회",
            "result": MalwareBazaar_Analysis_Result,
            "status": True  # 분석 결과 여부
        }
        print(analyzed_results["analyzed_results_"]["malwarebazaar"])
    #else:
    #    analyzed_results["analyzed_results_"]["malwarebazaar"] = {
    #        "description": "악성코드 DB 체크용 조회",
    #        "result": None,
    #        "status": False  # 분석 결과 여부
    #    }
    #print("MalwareBazaar_Analysis_Result 분석된")

    # 4. Yara
    Yara_Analysis_Result = analysis_service_instance.Yara_Analysis( # 무조건 성공처리 되어야함
                        analysis_target_bin=binary
                    ).get()
    if Yara_Analysis_Result:
        analyzed_results["analyzed_results_"]["yara"] = {
            "description": "Yara 악성코드 조회",
            "result": Yara_Analysis_Result,
            "status": True  # 분석 결과 여부
        }
        #print(analyzed_results["analyzed_results_"]["yara"])
    #else:
    #    analyzed_results["analyzed_results_"]["yara"] = {
    #        "description": "Yara 악성코드 조회",
    #        "result": None,
    #        "status": False  # 분석 결과 여부
    #    }
    #print("Yara_Analysis_Result 분석된")

    # 최종 결과 전송


    Return(
        queue_instance=queue_instance,
        analyzed_result=analyzed_results
    )

    return

# 반환
def Return(queue_instance:queue.Queue, analyzed_result:dict):
    #print(f"analyzed_result -> {analyzed_result}")
    queue_instance.put(analyzed_result)
    return

# init 시작
# Input 필수 구현 메서드
def Start_Analysis(analysis_service_instance: ToolManager, queue_instance:queue.Queue, DATA:dict):
    thread = threading.Thread(target=Start_File_Type_Analysis, args=(analysis_service_instance, queue_instance, DATA))
    thread.start()

    return queue_instance




# 하위 주석 -> 실제 스크립트 테스트 코드
'''import os
# 특정 폴더에 있는 exe파일 목록(절대경로) 가져오는것

Folder = r"E:\save_file"
file_list = []
for root, dirs, files in os.walk(Folder):
    for file in files:
        file_list.append(os.path.join(root, file))
print(file_list)

for file in file_list:
    test_exe_sample = b''
    print(f"{file} -> 처리 중")
    with open(file, 'rb') as f:
        test_exe_sample = f.read()


    queue_instance = queue.Queue()
    Start_File_Type_Analysis(
        analysis_service_instance=Provider_Analysis_service(),
        queue_instance=queue_instance,
        DATA={
                "binary": base64.b64encode(test_exe_sample).decode('utf-8')
            }
    )

    print(queue_instance.get())
    print(f"{file} -> 처리 완료")'''