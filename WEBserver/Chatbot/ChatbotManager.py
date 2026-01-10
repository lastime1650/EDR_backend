from starlette.websockets import WebSocket, WebSocketDisconnect
import json, time


# 웹 소켓 객체 매니저
from Chatbot.WebSocketManager import WebSocketManager

# LLM 매니저
from LLM.LLMManager import LLM_Manager

# EDR 매니저
from EDR.EDRManager import EDR_Manager

# 연관 분석기
from BehaviorAnalyzerManagement.BehaviorAnalzer import BehaviorAnalyzer

class ChatbotManager():
    def __init__(
        self,
        EDR_Manager:EDR_Manager, # -> 인수로 활용
        LLM_Manager:LLM_Manager, # -> 인수로 활용
        TreeBehaviorAnalyzer:BehaviorAnalyzer, # -> 인수로 활용
        ):
        
        # 1. 웹 소켓 객체 매니저
        self.WebSocketManager = WebSocketManager()
        
        # 2. 챗봇 Tool 
        from Chatbot.Chatbot_LLM_Management.ChatbotLLM_Tools import Chatbot_tools
        ChatbotTools = Chatbot_tools(
            websocket_manager=self.WebSocketManager,
            EDR_Manager=EDR_Manager,
            TreeBehaviorAnalyzer=TreeBehaviorAnalyzer,
            
        )
        
        # 3. 챗봇전용 LLM 매니저
        from Chatbot.Chatbot_LLM_Management.ChatbotLLM_Manager import Chatbot_LLM_Manager
        self.Chatbot_LLM_Manager = Chatbot_LLM_Manager(
                ChatbotTools=ChatbotTools,
                LLM_Manager=LLM_Manager
            )
        
    
    # FastAPI -(WebSocket 호출)-> WebSocketManager -> WebSocket(async처리요구)
    async def WebSocket(self, websocket:WebSocket):
        await websocket.accept()

        time.sleep(1) # 초기 처리 시간

        await self.init_client_process_(websocket) # 초기 통신

        while True:
            try:
                data = await websocket.receive_text() # JSON 구조로 송수신함. 수신된 데이터는 바로 에이전트 LLM에게..
                print(data)

                my_cookie = self.WebSocketManager.Get_my_Cookie(websocket) # LLM내 고유 메모리
                output_by_LLM = self.Chatbot_LLM_Manager.Start_ChatBot(query=data, history_key=my_cookie )# LLM에게 요청

                result = await self.WebSocketManager.Send_msg(my_cookie, output_by_LLM)
                print(f"WebSocket send -> {my_cookie}")

                #await websocket.send_text(output_by_LLM)


            except WebSocketDisconnect:
                # 이미 닫혀짐
                #self.remove_client_session_(websocket) # 세션 삭제
                break
            except Exception as e:
                print(e)
                #self.remove_client_session_(websocket) # 세션 삭제
                await websocket.close()
                break


    # 웹 소켓 연결 초기 처리
    async def init_client_process_(self, websocket:WebSocket):
        Client_Coockie_str: str = await websocket.receive_text() # await

        print(f"Client_Coockie_str -> {Client_Coockie_str} 웹 소켓 수신 받음")

        # 세션 추가 ( 이전에 쿠키가 등록되어 동일하여도 "덮어써야"한다. websocket객체가 달라졌으므로, 웹 소켓 객체를 바꾸는 것일 뿐이다. )
        self.WebSocketManager.set_client_session_(Client_Coockie_str, websocket)

        # 이전 대화 기록 가져오기
        # 이제 세션이 존재하며, 이전 대화를 가져오도록 한다. Q어디에서? -> self.chatbot_llm_manager() 객체로부터 Memory 이전 버퍼를 읽어서 가져와야함
        Previous_Conversation = self.Chatbot_LLM_Manager.get_previous_chat_history_(Client_Coockie_str) # LLM의 메모리에서 대화 이력을 가져온다.
        init_json = self.create_client_json( "init", Previous_Conversation )

        await websocket.send_text(init_json) # 초기화 메시지 전송

        return

    # 클라이언트 WebSocket에 전달하는 JSON규격을 생성하고 반환한다.
    def create_client_json(self, cmd:str, data:any)->str:
        return json.dumps({
            "cmd": cmd,
            "data": data
        }, ensure_ascii=False)
        