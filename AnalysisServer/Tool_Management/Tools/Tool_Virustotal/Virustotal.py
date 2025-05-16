import time
from typing import Optional, List, Dict
import queue, threading
import requests
import hashlib

class VirusTotal_analysis():
    def __init__(self, GLOBAL_API_KEY:str=""):
        self.available__analysed_json_keys = ["total_votes", "last_analysis_results", "sigma_analysis_stats", "detectiteasy", "packers", "tags", "sigma_analysis_results","last_analysis_stats", "sigma_analysis_summary","popular_threat_classification", ]

        self.GLOBAL_API_KEY = GLOBAL_API_KEY

    def Start_Analysis(self,API_KEY:str, FILE_DATA:bytes, opt_FILE_SHA256:str=None)->queue.Queue:
        new_queue = queue.Queue()
        threading.Thread(target=self._start_analysis, args=(API_KEY, FILE_DATA, new_queue, opt_FILE_SHA256), daemon=True).start()
        return new_queue

    def _start_analysis(self, API_KEY:str, FILE_DATA:bytes, output_queue:queue.Queue, opt_FILE_SHA256:str=None):#->Optional[dict]:
        file_sha256 = opt_FILE_SHA256
        if not file_sha256:
            file_sha256 = hashlib.sha256(FILE_DATA).hexdigest()

        # 이전에 분석한 이력이 있는 지 SHA256으로 먼저 요청

        searched_result = self._check_file(API_KEY, file_sha256)
        if not searched_result:
            if len(self.GLOBAL_API_KEY) > 0:
                searched_result = self._check_file(API_KEY, file_sha256)
                

        if searched_result:

            output_queue.put(searched_result) # output
        else:
            # 이전에 분석 이력이 없으면 FILE_DATA 파일을 직접 업로드
            # 새로 파일 업로드 ( 분석 완료까지 대기 해야함 )
            analysed_upload_result = self._upload_file(API_KEY, FILE_DATA)

            # 만약 None 반환된 경우, Free API로 시도
            if not analysed_upload_result:
                if len(self.GLOBAL_API_KEY) > 0:
                    analysed_upload_result = self._upload_file(API_KEY, FILE_DATA)

            output_queue.put(analysed_upload_result) # output

        return


    def _check_file(self, API_KEY:str, FILE_SHA256:str)->Optional[dict]:
        url = f"https://www.virustotal.com/api/v3/files/{FILE_SHA256}"

        headers = {
            "accept": "application/json",
            "x-apikey": API_KEY
        }

        output = dict( requests.get(url, headers=headers).json() )
        try:
            return self._available_analysed_keys_process(output)
        except:
            return None



    def _upload_file(self, API_KEY:str, FILE_DATA:bytes)->Optional[dict]:
        url = f"https://www.virustotal.com/api/v3/files/upload_url"
        body_param = {
            "file": FILE_DATA
        }
        headers = {
            "accept": "application/json",
            "x-apikey": API_KEY
        }
        upload_url = str( requests.get(url,headers=headers).json()["data"] ) # 대용량 파일을 분석하기 위한 임시 "분석 URL" 얻기

        analysis_id = requests.post(upload_url, headers=headers, files=body_param).json()#["data"]["id"] # 분석 파일 업로드 후 분석 결과 ID얻기 (조회용)

        if "data" not in analysis_id: # 실패시 {'error': {'code': 'QuotaExceededError', 'message': 'Quota exceeded'}}
            return None

        analysis_url = f"https://www.virustotal.com/api/v3/analyses/{analysis_id['data']['id']}"

        while True:
            # 분석 완료가 될 때 루프 탈출
            output = requests.get(analysis_url, headers=headers).json()

            if "data" not in output:
                print("VT API 사용한도가 초과되었거나 API 오류가 발생함")
                return None

            if output["data"]["attributes"]["status"] == "queued":
                time.sleep(0.5)
                continue
            else:
                break

        try:
            return self._available_analysed_keys_process(output)
        except:
            return None


    def _available_analysed_keys_process(self, input_analysed_json:dict)->Optional[dict]:
        try:
            # 필요한 것만

            for key, data in dict(input_analysed_json["data"]["attributes"]).items():
                if key not in self.available__analysed_json_keys:
                    del input_analysed_json["data"]["attributes"][key]
                    continue

                if "last_analysis_results" in key:
                    try:
                        for key2, data2 in input_analysed_json["data"]["attributes"]["last_analysis_results"].items():
                            input_analysed_json["data"]["attributes"]["last_analysis_results"][key2] = {
                                "method" : data2["method"],
                                "engine_name" : data2["engine_name"],
                                "category": data2["category"],
                                "result": data2["result"]
                            }
                    except:
                        return None


                elif "sigma_analysis_results" in key:
                    try:
                        new_sigma_analysis_results:List[Dict] = []
                        for i, sigma_rule_data in enumerate(list(input_analysed_json["data"]["attributes"]["sigma_analysis_results"])):
                            sigma_rule_data = dict(sigma_rule_data)

                            re_sigma_rule_data = {
                                "rule_level": sigma_rule_data["rule_level"],
                                "rule_source": sigma_rule_data["rule_source"],
                                "rule_title": sigma_rule_data["rule_title"],
                                "rule_description": sigma_rule_data["rule_description"],
                                "match_context": sigma_rule_data["match_context"],
                            }
                            new_sigma_analysis_results.append(re_sigma_rule_data)

                        input_analysed_json["data"]["attributes"]["sigma_analysis_results"] = new_sigma_analysis_results
                    except:
                        return None

            try:
                output = {
                    "type": input_analysed_json["data"]["type"],
                    "attributes": input_analysed_json["data"]["attributes"]
                }
                return output
            except:
                return None


        except:
            return None




'''result = \
    {
    'reason':
        "분석은 제공된 JSON 데이터의 'summary', 'tags', 'tech_summary', 'report_with_timeline' 필드를 기반으로 진행되었습니다.\
        타임스탬프 순서대로 이벤트를 나열하고, 각 이벤트의 설명과 기술적인 세부 정보를 종합하여 분석했습니다.  \
        Yara 탐지 결과는 참고 자료로 사용되었지만, 악성 여부 판단에는 사용되지 않았습니다.  \
        알 수 없는 실행 파일의 로드와 ntdll.dll에서의 디버거 탐지 회피 및 SEH 조작 관련 Yara 규칙 탐지는 추가 분석이 필요한 중요한 이벤트로 간주되었습니다.\
        다수의 시스템 DLL 로드는 시스템 동작의 일반적인 측면으로 간주되었지만,  시간적 집중도와 규모를 고려하여 기록하였습니다.\
        분석 과정에서 악성 행위 여부 판단은 배제하고, 관찰된 이벤트에 대한 기술적인 설명과 타임라인 정보에 집중했습니다."
}'''

