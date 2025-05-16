import threading
from typing import Optional, Dict

import requests
import json


class URLhaus():
    def __init__(self):
        self.mutex = threading.Lock()
        pass

    def IP_query(self, IP:str)->Optional[Dict]:
        api_url = "https://urlhaus-api.abuse.ch/v1/host/"
        payload_data = {"host": IP}
        return self.POST_QUERY(
            api_url=api_url,
            payload_data=payload_data
        )

    def URL_query(self, URL:str)->Optional[Dict]:
        api_url = "https://urlhaus-api.abuse.ch/v1/url/"
        payload_data = {"url": URL}
        return self.POST_QUERY(
            api_url=api_url,
            payload_data=payload_data
        )

    def POST_QUERY(self, api_url:str, payload_data:dict)->Optional[Dict]:
        with self.mutex:
            try:
                response = requests.post(api_url, data=payload_data)
                response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

                json_response = response.json()
                #if json_response["query_status"] == "no_results":
                    #return {"query_status":}

                return json_response

            except requests.exceptions.RequestException as e:
                print(f"Error during API request: {e}")
                return None


import threading, queue
class URLhaus_for_provider(URLhaus):
    def __init__(self):
        super().__init__()

    def Start_Analysis(self, analysis_target_IP:str)->queue.Queue:
        queue_inst = queue.Queue()
        thread = threading.Thread(target=self.Running, args=(analysis_target_IP, queue_inst))
        thread.start()
        return queue_inst


    def Running(self, analysis_target_IP:str, queue_inst:queue.Queue):
        result = {
            "URLhaus": {
                "IP_result": Optional[Dict],
                # "URL_result": None
            }
        }

        ip_query_result = self.IP_query(analysis_target_IP) # IP 조회
        
        # 실패
        if "query_status" in ip_query_result and ip_query_result["query_status"] == "no_results":
            queue_inst.put(None)
            return
        
        if ip_query_result:
            result["URLhaus"]["IP_result"] = ip_query_result
        else:
            #result["URLhaus"]["IP_result"] = {"status":"fail", "message":"no database here"}
            result = None

        queue_inst.put(result)
        return
