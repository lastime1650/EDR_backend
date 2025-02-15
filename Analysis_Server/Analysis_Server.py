import json
import struct
import threading
import time
from typing import Optional

import uvicorn
from pydantic import BaseModel
import fastapi
from fastapi import FastAPI, HTTPException, Query, APIRouter, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from _Analysis_Server_.AGENT_INSTANCE.Agent_based_instance import Agent_instance_manager
from _Analysis_Server_.SCRIPT_PACKAGES.Script_Packages import Script_Packages, Script_Packages_type_enum

'''
    RestAPI 로 구동되는 분석 서버.
    에이전트, 사용자(GUI)와 통신한다. 
'''
class _Analysis_Server_:
    def __init__(self, serverip:str, serverport:int):

        '''
            [0] 필요한 인스턴스를 load한다.
        '''

        # 스크립트 패키지 매니저
        self.Script_Packages = Script_Packages()

        # 에이전트 인스턴스 매니저
        self.Agent_instance_manager = Agent_instance_manager(self.Script_Packages)



        self.serverip = serverip
        self.serverport = serverport
        self.app = FastAPI()
        self.app_router = APIRouter()

        self.setup_routes() # RESTAPI url 설정
        self.app.include_router(self.app_router)
        return

    def setup_routes(self):

        # 분석 요청 (길이 기반 데이터로 통신) ([]byte)
        self.app_router.post("/API/Analysis_Request")(self.Analysis_Request)

        # 에이전트 등록 ( JSON)
        self.app_router.get("/API/Agent_Register")(self.Agent_Register)
        # 에이전트 삭제 ( JSON)
        self.app_router.get("/API/Agent_Remove")(self.Agent_Remove)


        # 스크립트 추가 ( JSON)
        self.app_router.post("/API/Script_Register")(self.Script_Register)
        # 스크립트 삭제 ( JSON)
        self.app_router.get("/API/Script_Remove")(self.Script_Remove)


        # 스크립트 정보 보기 ( JSON)
        self.app_router.get("/API/Script_Info")(self.Script_Info)

        return

    #-------------------------------------------------------------------------------------------------------------------
    # 분석 요청 ( 단, 에이전트 등록이 되어 있어야함 )
    # 데이터는 길이기반 통신이다.
    # 다음과 같은 구조를 가진다.

    # [1]에이전트 ID
    # [2]스크립트 타입
    # [3]분석 대상 데이터
    async def Analysis_Request(self, Request_Data:bytes = Body(None)):
        '''
        {
            "AGENT_ID": "ABC",
            "SCRIPT_TYPE": "file",
            "DATA": {
                /* "SCRIPT_TYPE" 에따라 key가 다를 수 있다. 예를 들어 Network의 경우에는 "REMOTE_IP"가 key로 전달되고, 'binary'가 포함되지 않을 수 있다 */

                "binary": base64.b64encode(test_exe_sample).decode('utf-8')
                또는
                "REMOTE_IP": "8.8.8.8"(str)
            }
        }
        '''
        recv_json = dict(json.loads(Request_Data))
        if "binary" in recv_json:
            print("바이너리 존재함.")
        else:
            print("바이너리 없음")
        # 분석 요청..
        return self.Agent_instance_manager.Request_Analysis(

            str(recv_json["AGENT_ID"]),
            str(recv_json["SCRIPT_TYPE"]),
            dict(recv_json["DATA"])

        )
        # 분석 요청..
        #return self.Agent_instance_manager.Request_Analysis( agent_id, script_type, analysis_data,)



    # -------------------------------------------------------------------------------------------------------------------

    # 분석서버에 에이전트를 기본등록함.
    async def Agent_Register(self, input_JSON:Optional[str] = Query(None)):
        '''
            Request_JSON = {
                "AGENT_ID": str() (등록, 이미 등록된 경우 실패 반환 )
            }
        '''
        RestAPI_request:dict = json.loads(input_JSON)

        if not "AGENT_ID" in RestAPI_request:
            return {"status":"fail", "message":"AGENT_ID 키가 없습니다. "}

        AGENT_ID = RestAPI_request["AGENT_ID"]

        if self.Agent_instance_manager.Add_Agent(AGENT_ID):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"에이전트 등록 실패 또는 이미 존재합니다."}
    # 에이전트 삭제
    async def Agent_Remove(self, input_JSON:Optional[str] = Query(None)):
        '''
            input_JSON = {
                "AGENT_ID": str()
                // 하나 필요
            }
        '''

        input_JSON = json.loads(input_JSON)

        if input_JSON is None or "AGENT_ID" not in input_JSON:
            return {"status":"fail", "message":"AGENT_ID 키가 없습니다. "}


        AGENT_ID = input_JSON["AGENT_ID"]

        if self.Agent_instance_manager.Remove_Agent(AGENT_ID):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"에이전트 삭제 실패 또는 존재하지 않습니다."}


    # 분석서버에 이미 등록된 에이전트에 스크립트를 등록함
    async def Script_Register(self, SCRIPT_NAME: str = Body(...), SCRIPT_TYPE: str = Body(...), SCRIPT_PYTHON_CODE: str = Body(...)):
        '''
            "SCRIPT_NAME": str(), // 추가할 스크립트 이름
            "SCRIPT_TYPE": str(), // 스크립트 타입
            "SCRIPT_PYTHON_CODE": str() // 파이썬 코드

            # POST 방식으로 변경됨
        '''
        SCRIPT_NAME = SCRIPT_NAME.lower()
        SCRIPT_TYPE = SCRIPT_TYPE
        SCRIPT_PYTHON_CODE = SCRIPT_PYTHON_CODE

        # 이미 스크립트가 존재하는 지 확인한다.
        if self.Script_Packages.Get_script(Script_Packages_type_enum[SCRIPT_TYPE], SCRIPT_NAME):
            return {"status":"fail", "message":"이미 존재하는 스크립트입니다."}

        # 스크립트 등록한다.
        if self.Script_Packages.Add_Script(SCRIPT_NAME, Script_Packages_type_enum[SCRIPT_TYPE], SCRIPT_PYTHON_CODE):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"스크립트 등록 실패"}

    # 스크립트 삭제
    async def Script_Remove(self, input_JSON:Optional[str] = Query(None)):
        '''
            input_JSON = {
                "SCRIPT_NAME": str()
                // 하나 필요
            }

            *삭제 시도시, 다른 에이전트에 의해 분석중인 경우, 끝날때까지 기다려야하므로 딜레이가 발생할 수 있다. (Mutex) *
        '''
        RestAPI_request: dict = json.loads(input_JSON)

        SCRIPT_NAME = RestAPI_request["SCRIPT_NAME"].lower()

        if self.Script_Packages.Remove_script(SCRIPT_NAME):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"스크립트 등록 실패"}

    # -------------------------------------------------------------------------------------------------------------------
    # 스크립트 정보 보기
    async def Script_Info(self, input_JSON:Optional[str] = Query(None)):
        '''
            Request_JSON = {
                "SCRIPT_NAME": str() // 없는 경우, SCRIPT_TYPE기준으로
                "SCRIPT_TYPE": str() // 없는 경우, SCRIPT_NAME기준으로
                // 둘다 있는 경우, 일치한지 보게 된다.
            }
        '''
        RestAPI_request:dict = json.loads(input_JSON)
        if not "SCRIPT_TYPE" in RestAPI_request :
            if not "SCRIPT_NAME" in RestAPI_request:
                return {"status":"fail", "message":"SCRIPT_NAME 또는 SCRIPT_TYPE 키가 없습니다. "}
            else:
                # NAME만 있는 경우
                r = self.Script_Packages.Get_script(None,RestAPI_request["SCRIPT_NAME"])
                return {"status":"success", "message":r}
        else:
            if not "SCRIPT_NAME" in RestAPI_request:
                # TYPE만 있는 경우
                r = self.Script_Packages.Get_script(Script_Packages_type_enum[RestAPI_request["SCRIPT_TYPE"]], None)
                return {"status": "success", "message": r}
            else:
                # TYPE, NAME 모두 있는 경우
                r = self.Script_Packages.Get_script(Script_Packages_type_enum[RestAPI_request["SCRIPT_TYPE"]], RestAPI_request["SCRIPT_NAME"])
                return {"status":"success", "message":r}


    def start_web(self):
        uvicorn.run(self.app, host=self.serverip, port=self.serverport)
        return

def main():
    app = _Analysis_Server_("127.0.0.1", 5070)
    app.start_web()

if __name__ == "__main__":
    threading.Thread(target=main).start()
    time.sleep(1)

    # Default Script 추가  (기본 EDR 제공형)
    import _Analysis_Server_.default_script_setting.default_script_module as default_script_module
    default_script_module.Init_Input_Script() # 기본 제공형 스크립트 추가

    '''# 테스트 ...
    import requests, json, base64

    # 에이전트 추가
    input_JSON = {
        "AGENT_ID": "ABC"
    }
    url = "http://127.0.0.1:5070/API/Agent_Register"
    r = requests.get(url, params={"input_JSON": json.dumps(input_JSON)}).text
    print(r)

    # 에이전트 제거
    input_JSON = {
        "AGENT_ID": "ABC"
    }
    url = "http://127.0.0.1:5070/API/Agent_Remove"
    r = requests.get(url, params={"input_JSON": json.dumps(input_JSON)}).text
    print(r)

    # 스크립트 제거
    input_JSON = {
        "SCRIPT_NAME": "default1"
    }
    url = "http://127.0.0.1:5070/API/Script_Remove"
    r = requests.get(url, params={"input_JSON": json.dumps(input_JSON)}).text
    print(r)
'''


    '''url = "http://127.0.0.1:5070/API/Analysis_Request"
    test_exe_sample = b''
    with open("C:\\Users\\Administrator\\Desktop\\KDU\kdu.exe", 'rb') as f:
        test_exe_sample = f.read()

    request_data = json.dumps(
        {
            "AGENT_ID": "ABC",
            "SCRIPT_TYPE": "file",
            "DATA": {
                "binary": base64.b64encode(test_exe_sample).decode('utf-8')
            }
        }
    )
    #print(request_data)
    headers = {"Content-Type": "application/octet-stream"}  # 바이너리 데이터 전송을 위한 헤더
    response = requests.post(url, data=request_data, headers=headers)
    print(response.text)'''

'''
import requests

#----

req = {
    "AGENT_ID": "ABC"
}
r = requests.get('http://127.0.0.1:5070/API/Agent_Register', params={'input_JSON':str(json.dumps(req))}).text
print(r)

r = requests.get('http://127.0.0.1:5070/API/Agent_Register', params={'input_JSON':str(json.dumps(req))}).text
print(r)

#----

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
req = {
    "SCRIPT_NAME": "ABC",
    "SCRIPT_TYPE": "file",
    "SCRIPT_PYTHON_CODE": python_code_for_a_sample
}
print(json.dumps(req))
headers = {'Content-Type': 'application/json'}
r = requests.post('http://127.0.0.1:5070/API/Script_Register', headers=headers,data=json.dumps(req)).text
print(r)


req = {
    "SCRIPT_NAME": "ABC",
    "SCRIPT_TYPE": "file",
}

r = requests.get('http://127.0.0.1:5070/API/Script_Info', params={'input_JSON':str(json.dumps(req))}).text
print(r)


def send_analysis_request(agent_id, script_type, analysis_data, url):
    """
    requests를 사용하여 Analysis_Request 함수에 POST 요청을 보내는 함수입니다.

    Args:
        agent_id (str): 에이전트 ID
        script_type (str): 스크립트 타입 (Script_Packages_type_enum의 멤버 중 하나)
        analysis_data (bytes): 분석 대상 데이터
        url (str): 요청을 보낼 URL (예: "http://localhost:8000/Analysis_Request")

    Returns:
        requests.Response: 서버로부터의 응답 객체
    """

    # 1. 길이 기반 데이터 생성
    request_data = b""

    # [1] 에이전트 ID 길이 및 데이터 추가
    agent_id_bytes = agent_id.encode()
    request_data += struct.pack("<I", len(agent_id_bytes))
    request_data += agent_id_bytes

    # [2] 스크립트 타입 길이 및 데이터 추가
    script_type_bytes = script_type.encode()
    request_data += struct.pack("<I", len(script_type_bytes))
    request_data += script_type_bytes

    # [3] 분석 데이터 길이 및 데이터 추가
    request_data += struct.pack("<I", len(analysis_data))
    request_data += analysis_data

    # 2. requests를 사용하여 POST 요청 전송
    headers = {"Content-Type": "application/octet-stream"}  # 바이너리 데이터 전송을 위한 헤더
    response = requests.post(url, data=request_data, headers=headers)

    return response

# 사용 예시
agent_id = "ABC"
script_type = "file"  # Script_Packages_type_enum에 정의된 값 중 하나
analysis_data = b"This is the data to be analyzed."
url = "http://127.0.0.1:5070/API/Analysis_Request"  # FastAPI 서버의 URL로 변경

response = send_analysis_request(agent_id, script_type, analysis_data, url)

# 응답 확인
if response.status_code == 200:
    print("요청 성공:", response.content)
else:
    print("요청 실패:", response.status_code)
'''
