# LLM RESTAPI 서버
import asyncio
from typing import Optional, List

import uvicorn
from pydantic import BaseModel
import fastapi
from fastapi import FastAPI, HTTPException, Query, APIRouter, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json

from starlette.websockets import WebSocket, WebSocketDisconnect

##
from _LLM_Server_.LLM_Management_LLM.Manager import LLM_Manager
from _LLM_Server_.llm_enum import LLM_req_Type
from _LLM_Server_.LLM_Management_LLM.LLM_clustering.LLM_Cluster import LLM_Cluster, Available_LLM_Models


# RestAPI 서버
class LLM_Server:
    def __init__(self, host: str, port: int):
        self.serverip = host
        self.serverport = port

        self.app = FastAPI()
        self.router = APIRouter()

        self.setup_routes() # RESTAPI url 설정
        self.app.include_router(self.router)



        # 전역 인스턴스
        self.LLM_Cluster = LLM_Cluster()

        self.LLM_Manager = LLM_Manager() # LLM 총 관리 인스턴스

    def setup_routes(self):
        # 종합평가 요청
        self.router.post("/api/LLM_EVAL")(self.LLM_EVAL)

        # LLM 추가
        self.router.get("/api/LLM_Register")(self.LLM_Register)
        # LLM 제거
        self.router.get("/api/LLM_Remove")(self.LLM_Remove)

        # 등록된 LLM 목록 가져오기
        self.router.get("/api/LLM_Registered")(self.LLM_Registered)

##########################################################################################################################
        # -- websocket(챗봇) 수신 부
        self.router.websocket("/ws")(self.ws)



    # 종합평가
    async def LLM_EVAL(self, input_JSON:bytes =Body(...)):
        output = {"status":"failed", "response":{}}
        '''
            종합평가를 실시하는 서버
            input_JSON = {
                "cmd": "ALL_EVAL", // 문자열 매칭 -> ALL_EVAL, MIDDLE_EVAL, FINAL_EVAL // TYPE_EVAL 총 4개 지원
                "instance_id": "core-server의 프로세스 인스턴스 id", 
                
                "data": {/*여기는 종합평가요청할 << JSON >> 데이터*/}
            }
        '''
        SUCCESS = "success"
        FAIL = "fail"
        output_json_form = {"status": "", "response": ""}

        parsedJSON = json.loads(input_JSON)# encoded_json 처리
        #print(f"parsedJSON -> {parsedJSON}")

        if ("cmd" in parsedJSON) and ("data" in parsedJSON) and ("instance_id" in parsedJSON):
            cmd = str(parsedJSON["cmd"]).upper()
            data = str(parsedJSON["data"])
            instance_id = str(parsedJSON["instance_id"]) # 중간평가+최종평가에만 활용된다. 이는 LLML의 메모리 버퍼 인스턴스 식별값

            # 명령을 식별하여 평가를 요청한다.
            result_bool, result_message =self.LLM_Manager.Start_Evaluation(LLM_req_Type[cmd], data, instance_id) # LLM 평가 수행

            if result_bool:
                output_json_form["status"] = SUCCESS
            else:
                output_json_form["status"] = FAIL

            output_json_form["response"] = result_message

        else:
            output_json_form["status"] = FAIL
            output_json_form["response"] = "잘못된 요청입니다. 정보를 다시 입력해주세요."

        return output_json_form

    # LLM 추가
    async def LLM_Register(self, input_JSON:Optional[str] =Query(...)):

        '''
            {
                "NAME": "", // 사용자 정의 ID
                "MODEL_TYPE": "", // 모델 타입 (지원가능한 LLM)
                "METADATA": {} // 불투명 하지만, MODEL_TYPE에 따라 데이터
            }
        '''
        parsedJSON = json.loads(input_JSON)

        NAME = str(parsedJSON["NAME"])
        MODEL_TYPE = str(parsedJSON["MODEL_TYPE"]).lower()
        METADATA = {}
        try:
            METADATA = json.loads(parsedJSON["METADATA"])
        except:
            METADATA = dict(parsedJSON["METADATA"])

        return self.LLM_Cluster.Add_Model(
            NAME=NAME,
            MODEL_TYPE=Available_LLM_Models[MODEL_TYPE], # LLM_Cluster 에서 지원가능한 LLM 모델 enum 타입
            METADATA=METADATA
        )

    # LLM 모델 삭제
    async def LLM_Remove(self, input_JSON:Optional[str] =Query(...)):
        '''
            {
                "NAME": "", // 사용자 정의 ID ( 이전에 등록한 모델 닉네임(ID) )
            }
        '''
        input_json = json.loads(input_JSON)
        MODEL_NAME = str(input_json["NAME"])
        return self.LLM_Cluster.Remove_Model(MODEL_NAME)


    ##########################################################################################################################

    # 웹 소켓 지속 수신부
    # WebSocket(챗봇) 수신 부
    async def ws(self, websocket: WebSocket):
        await websocket.accept()

        # 초기 통신을 수행한다.
        # 1. 클라이언트의 정보 (로그인된 Cookie 문자열) 수신 받아야한다.
        Client_Coockie_str: str = await asyncio.wait_for(websocket.receive_text(), timeout=60)  # 1분
        print(f"Client_Coockie_str -> {Client_Coockie_str} 웹 소켓 수신 받음")
        # 클라이언트의 쿠키를 얻음

        # 2. 이전 대화 이력이 있는 경우, 대화 이력을 송신 한다.
        previous_chat_history = {
            "cmd":"init",
            "messages": []
        }
        conversationbuff =  self.LLM_Manager.ALL_EVAL.Share_Agent_Chatbot_Memory_Manager.Get_Conversation(Client_Coockie_str)
        if conversationbuff:
            print(f"이전 대화 -> {previous_chat_history}")
            '''
            [
                {
                    "user": "사용자 요청 쿼리",
                    "ai": "사용자 요청 쿼리에 대한 LLM 응답"
                },,,,,, + ㄴ
            ]
            '''
            previous_chat_history["messages"] = self.LLM_Manager.ALL_EVAL.Share_Agent_Chatbot_Memory_Manager.output_Conversation_history(conversationbuff)
        # 3. init 송신
        await websocket.send_json(previous_chat_history)


        # WebSocket 세션 등록
        self.LLM_Manager.ALL_EVAL.Agent_Chatbot_manager.WebSocket_Manager\
            .Add_WebSocket_instance(
            WebSocket_id=Client_Coockie_str,
            WebSocket=websocket
        )

        # 세션 Thread는 계속 유지 시켜줘야한다.
        try:
            while True:
                recevied_json:dict = await websocket.receive_json()



                SESSION_ID = websocket.cookies.get("logged_cookie") # 현재 사용자의 쿠키 값
                user_says = str(recevied_json["user"]) # 현재 사용자가 입력한 메시지
                current_page = str(recevied_json["current_page"]) # 현재 사용자가 접속한 페이지

                result_status,  output_string = self.LLM_Manager.Start_Agent_Chatbot(
                    Chatbot_Session_ID=SESSION_ID,
                    Input_string=user_says,
                    Current_Page=current_page
                )

                await websocket.send_text(output_string)

        except WebSocketDisconnect:
            pass
        except Exception as e:
            await websocket.close()

        # 연결 종료 시 해제
        self.LLM_Manager.ALL_EVAL.Agent_Chatbot_manager.WebSocket_Manager \
            .Remove_WebSocket_instance(
            WebSocket_id=Client_Coockie_str
        )

        return
    #--
    # LLM 정보 가져오기
    async def LLM_Registered(self, request: Request):
        output: List[dict] = []
        for llm_info in self.LLM_Cluster.LLM_info["LLM"]:

            info:dict = self.LLM_Cluster.LLM_info["LLM"][llm_info]

            tmp = {
                "NAME" : llm_info
            }

            for key in info:
                if key != "MODEL" and key != "mutex":
                    tmp[key] = info[key]

            output.append(tmp)
        return output

    #--
    def Run(self):
        import uvicorn
        uvicorn.run(self.app, host=self.serverip, port=self.serverport)
        return


import threading

while True:
    try:
        test_instance = LLM_Server("192.168.0.1", 4060)

        test_instance.Run()

    except:
        pass

