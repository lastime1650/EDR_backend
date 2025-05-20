import asyncio
import threading
from typing import Optional

from starlette.websockets import WebSocket, WebSocketDisconnect

# 연결된 웹 소켓 클라이언트 관리 클래스
# { 쿠키값: WebSocket } 쌍으로 관리한다
class WebSocketManager:
    def __init__(self):
        self.client_ws_session = {}
        '''
            client_ws_session = {
                "Client_Coockie_str": WebSocket
            } ,,,
        '''
        self.mutex_ = threading.Lock()

    # 웹 소켓을 통해서 받은 쿠키를 리턴한다.
    def Get_my_Cookie(self, my_websocket:WebSocket)->Optional[str]:
        with self.mutex_:
            for cookie_name, websocket in self.client_ws_session.items():
                if websocket == my_websocket:
                    return cookie_name
            return ""
    def Get_my_WebSocket(self, my_cookie:str)->Optional[WebSocket]:
        with self.mutex_:
            if my_cookie in self.client_ws_session:
                return self.client_ws_session[my_cookie]
            else:
                return None

    async def Send_msg(self, my_cookie:str, data:str)->bool:
        with self.mutex_:
            if my_cookie in self.client_ws_session:
                try:
                    await self.client_ws_session[my_cookie].send_text(data)
                    return True
                except Exception as e:
                    print(f"WebSocket Send Error: {e}")
                    return False
            else:
                print("WebSocket not found")
                return False

    # Helper 함수
    # 전용 코루틴 처리 스레드에서 비동기 함수를 실행하기 위한 헬퍼 함수 ( 주로 LLM 에이전트 도구에서 await 대용으로 사용)
    # await할 코루틴 객체를 인자로 준비한 후, ,,, threading.Thread로 이 메서드를 호출해야한다.
    def Run_Async_corutine_object_(self, coro):
        try:
            asyncio.run(coro)
        except Exception as e:
            # 백그라운드 스레드에서 발생한 오류 로깅 (중요!)
            print(f"[Background Thread Error] WebSocket 전송 실패: {e}")


    # 내장 함수
    # 세션 체크
    def check_exists_client_session_(self, Client_Coockie_str:str)->Optional[bool]:
        with self.mutex_:
            if Client_Coockie_str in self.client_ws_session:
                return True
            else:
                return False
    # 세션 등록
    def set_client_session_(self, Client_Coockie_str:str, websocket:WebSocket):
        with self.mutex_:
            self.client_ws_session[Client_Coockie_str] = websocket
            print(f"Client_Coockie_str -> {Client_Coockie_str} 웹 소켓 추가")

    # 세션 삭제
    def remove_client_session_by_websocket_(self, websocket:WebSocket):
        with self.mutex_:
            for cookie_id, value in self.client_ws_session.items():
                if value == websocket:
                    del self.client_ws_session[cookie_id]
                    print(f"Client_Coockie_str -> {cookie_id} 웹 소켓 삭제")


                    break
    def remove_client_session_by_cookie_id_(self, cookie_id:str):
        with self.mutex_:
            if cookie_id in self.client_ws_session:
                del self.client_ws_session[cookie_id]
                print(f"Client_Coockie_str -> {cookie_id} 웹 소켓 삭제")

