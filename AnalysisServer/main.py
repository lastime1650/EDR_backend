import json
import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, APIRouter, Body, Request


# analysis enum
from ScriptManagement.globalenum import Script_Packages_type_enum

from ScriptManagement.ScriptManager import ScriptManager

class _Analysis_Server_:
    def __init__(
        self, 
        
        analysis_server_host:str, 
        elasticsearch_host:str,
        
        
        
        analysis_server_port:int=6060,
        elasticsearch_port:int=9200,
        
        ):
        self.serverip = analysis_server_host
        self.serverport = analysis_server_port
        self.app = FastAPI()
        self.app_router = APIRouter()
        
        
        # 스크립트 매니저
        
        self.ScriptManager = ScriptManager(
            elasticsearch_host=elasticsearch_host,
            elasticsearch_port=elasticsearch_port
        )
        
        
        
        self.setup_routes() # RESTAPI url 설정
        self.app.include_router(self.app_router)
        
    def setup_routes(self):
        
        # 분석 요청 (길이 기반 데이터로 통신) ([]byte)
        self.app_router.post("/API/Analysis_Request")(self.Analysis_Request)

        # 분석 완료 확인
        self.app_router.get("/API/Check_Analysis_Result")(self.Check_Analysis_Result)



        # 스크립트 추가 ( JSON)
        self.app_router.post("/API/Script_Register")(self.Script_Register)
        # 스크립트 삭제 ( JSON)
        self.app_router.get("/API/Script_Remove")(self.Script_Remove)
        # 스크립트 정보 보기 ( JSON)
        self.app_router.get("/API/Get_All_Scripts")(self.Get_All_Scripts)
    
    def start_web(self):
        uvicorn.run(self.app, host=self.serverip, port=self.serverport, access_log=False) # access_log=False -> log안보이게
        return

    # 분석 요청
    async def Analysis_Request(self, input_JSON:bytes = Body(None)):
        
        
        received = json.loads(input_JSON)
        
        Script_Type = Script_Packages_type_enum[ str(received["SCRIPT_TYPE"])  ]
        DATA = dict( received["DATA"] ) 
        
        # 비동기 분석 / 결과는 ElasticSearch에 저장.
        
        threading.Thread(target=self.ScriptManager.Start_Analysis, args=(Script_Type, DATA)).start()
        
        return {"status":"success", "message":"요청된"}
    
    
    # 분석 완료 확인
    async def Check_Analysis_Result(self, input_JSON:Optional[str] = Query(None)):
        
        received = json.loads(input_JSON)
        
        result = self.ScriptManager.Get_Analysis_Result_(
            script_type=str(received["SCRIPT_TYPE"]),
            DATA=received["DATA"]
        )
        
        return {"status":"success", "message":"성공", "result":result}
        
        
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
        if self.ScriptManager.Get_script(Script_Packages_type_enum[SCRIPT_TYPE], SCRIPT_NAME):
            return {"status":"fail", "message":"이미 존재하는 스크립트입니다."}

        # 스크립트 등록한다.
        if self.ScriptManager.Add_Script(SCRIPT_NAME, Script_Packages_type_enum[SCRIPT_TYPE], SCRIPT_PYTHON_CODE):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"스크립트 등록 실패"}

    # 스크립트 삭제 (queue방식)
    async def Script_Remove(self, input_JSON:Optional[str] = Query(None)):
        
        RestAPI_request: dict = json.loads(input_JSON)

        SCRIPT_NAME = RestAPI_request["SCRIPT_NAME"].lower()

        if self.ScriptManager.Remove_script(SCRIPT_NAME):
            return {"status":"success", "message":"성공"}
        else:
            return {"status":"fail", "message":"스크립트 등록 실패"}
        
        
    async def Get_All_Scripts(self, request: Request):
        return { "status":"success", "message": self.ScriptManager.Get_all_scripts() }


# docker 이미지 - 환경변수 얻기
import os

analysis_server_host = os.environ.get("ANALYSIS_SERVER_HOST", "0.0.0.0")
analysis_server_port = os.environ.get("ANALYSIS_SERVER_PORT", "6060")
elasticsearch_host = os.environ.get("ELASTICSEARCH_HOST", "0.0.0.0") # 기본값 도메인(호스트명) 이름
elasticsearch_port = os.environ.get("ELASTICSEARCH_PORT", "9200")

print("Analysis Server 환경변수 체크 시작")
print(f"analysis_server_host -> {analysis_server_host}")
print(f"analysis_server_port -> {analysis_server_port}")
print(f"elasticsearch_host -> {elasticsearch_host}")
print(f"elasticsearch_port -> {elasticsearch_port}")
print("Analysis Server 환경변수 체크 끝")

app = _Analysis_Server_(
    analysis_server_host=analysis_server_host,
    analysis_server_port=int(analysis_server_port),
    elasticsearch_host=elasticsearch_host,
    elasticsearch_port=int(elasticsearch_port)
    
    )

threading.Thread(target=app.start_web).start()



import requests, time

time.sleep(1.5)

# 미리 준비된 스크립트 등록
SAMPLE_PATH = ""
SAMPLE_PYTHON_CODE = ""
REQUEST_DICT = {}

# 파일 유형
SAMPLE_PATH = "/docker__AnalysisServer/script_samples/file/sample_file.py" # /docker__AnalysisServer -> 도커파일 - 절대경로

#SAMPLE_PATH = "script_samples/file/sample_file.py"
SAMPLE_PYTHON_CODE = str( open(SAMPLE_PATH, 'r', encoding='utf-8').read() ) # 스크립트니까 사람이 읽을 수 잇음
REQUEST_DICT = {
    "SCRIPT_NAME": "default1",
    "SCRIPT_TYPE": "file",
    "SCRIPT_PYTHON_CODE": SAMPLE_PYTHON_CODE
}
headers = {'Content-Type': 'application/json'}
r = requests.post(f'http://{analysis_server_host}:{analysis_server_port}/API/Script_Register', headers=headers, data=json.dumps(REQUEST_DICT)).text
print(r)





# 네트워크 유형
SAMPLE_PATH = "/docker__AnalysisServer/script_samples/network/sample_network.py" # /docker__AnalysisServer -> 도커파일 - 절대경로
#SAMPLE_PATH = "script_samples/network/sample_network.py"
SAMPLE_PYTHON_CODE = str( open(SAMPLE_PATH, 'r', encoding='utf-8').read() ) # 스크립트니까 사람이 읽을 수 잇음
REQUEST_DICT = {
    "SCRIPT_NAME": "default2",
    "SCRIPT_TYPE": "network",
    "SCRIPT_PYTHON_CODE": SAMPLE_PYTHON_CODE
}
headers = {'Content-Type': 'application/json'}
r = requests.post(f'http://{analysis_server_host}:{analysis_server_port}/API/Script_Register', headers=headers, data=json.dumps(REQUEST_DICT)).text
print(r)


#
# TEST
#

'''url = f"http://{analysis_server_host}:{analysis_server_port}/API/Analysis_Request"

# file - TEST 
import base64
test_exe_sample = b''
with open(r"C:/Share/x.exe", 'rb') as f:
    test_exe_sample = f.read()
request_data = json.dumps(
            {
                "SCRIPT_TYPE": "file",
                "DATA": {
                    "binary": base64.b64encode(test_exe_sample).decode('utf-8')
                }
            }
        )
headers = {"Content-Type": "application/octet-stream"}
response = requests.post(url, data=request_data, headers=headers)
#print(response.text)
print(response.text)
'''


# network - TEST
'''url = f"http://{analysis_server_host}:{analysis_server_port}/API/Analysis_Request"

request_data = json.dumps(
            {
                "SCRIPT_TYPE": "network",
                "DATA": {
                    "remoteip": "8.8.8.8"
                }
            }
        )
headers = {"Content-Type": "application/octet-stream"}
response = requests.post(url, data=request_data, headers=headers)
#print(response.text)
print(response.text)'''