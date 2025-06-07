import json
import threading
from typing import Optional

import uvicorn
from fastapi import FastAPI, Query, APIRouter, Body, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import Response, RedirectResponse

class WebServer:
    def __init__(
        self, 
        
        CoreServer_host: str, 
        CoreServer_port: int,
        
        ElasticSearch_host: str, 
        
        Kibana_host: str,
        
        ElasticSearch_port: int=9200,
        Kibana_port: int=5601,
        
        WEB_host: str="0.0.0.0", 
        WEB_port: int=8000,
        
        WebSocket_External_Host: str="0.0.0.0", # --> 인터넷 외부 클라이언트인 경우, 직접 조정해줘야함 ( 웹 클라이언트에 적용될 웹 소켓 서버 IP를 지정하는 것임)
        #WebSocket_External_Port: int=8000, --. 포트는 WEB_port와 같음
        
        ):
        self.WEB_port = WEB_port
        self.WEB_host = WEB_host
        
        self.WebSocket_External_Host = WebSocket_External_Host
        
        self.CoreServer_host = CoreServer_host
        self.CoreServer_port = CoreServer_port
        
        self.ElasticSearch_host = ElasticSearch_host
        self.ElasticSearch_port = ElasticSearch_port
        
        self.Kibana_host = Kibana_host
        self.Kibana_port = Kibana_port
        
        # HTML 템플릿
        self.Template = Jinja2Templates(directory="/docker__WEBserver/templates")
        
        
        # ## 리소스 ## #
        
        # WEB 매니저
        from WebManagement.WebManager import WebManager # ㅇ
        self.WebManager = WebManager()
        
        # LLM 매니저
        from LLM.LLMManager import LLM_Manager # ㅇ
        self.LLM_Manager = LLM_Manager()
        
        # EDR 매니저 ( 코어서버 + 엘라스틱서치 + 키바나 통합 매니저)
        from EDR.EDRManager import EDR_Manager
        self.EDR_Manager = EDR_Manager(
            
            CoreServer_host=CoreServer_host,
            CoreServer_port=CoreServer_port,
            
            ElasticSearch_host=ElasticSearch_host,
            ElasticSearch_port=ElasticSearch_port,
            
            Kibana_host=Kibana_host,
            Kibana_port=Kibana_port,
            
        )
        
        
        # -- 연계 형 서비스 -- #
        
        
        
        # 시그마 룰 ( EDR 매니저 연계 -> 엘라스틱서치 필요 )
        from BehaviorAnalyzerManagement.SigmaManagement.Sigma_Manager import Sigma_Manager
        self.Sigma_Manager = Sigma_Manager(
            es=self.EDR_Manager.ElasticsearchAPI,
            Root_Directory="/docker__WEBserver/BehaviorAnalyzerManagement/SigmaManagement/sigma_all_rules/rules"
        )
        
        # 행위 분석 로그 관리
        from BehaviorAnalyzerManagement.Behavior_Elasticsearch import Behavior_ElasticSearch
        behavior_elasticsearch = Behavior_ElasticSearch(
            elastichost=self.EDR_Manager.ElasticSearch_host,
            elasticport=self.EDR_Manager.ElasticSearch_port,
        )
        
        # 행위 분석 매니저 ( LLM 매니저 + EDR 매니저 연계 )
        from BehaviorAnalyzerManagement.BehaviorAnalzer import BehaviorAnalyzer
        self.BehaviorAnalzer = BehaviorAnalyzer(
            Sigma_Manager=self.Sigma_Manager,
            EDR_Manager=self.EDR_Manager,
            LLM_Manager=self.LLM_Manager,
            behavior_elasticsearch=behavior_elasticsearch,
        )
        
        
        # 챗봇 매니저 ( LLM 매니저 연계 )
        from Chatbot.ChatbotManager import ChatbotManager
        self.ChatbotManager = ChatbotManager(
            EDR_Manager=self.EDR_Manager,
            LLM_Manager=self.LLM_Manager,
            TreeBehaviorAnalyzer=self.BehaviorAnalzer,
        )
        
        # app
        self.app = FastAPI()
        
        # 라우터
        self.add_router()
        
        # Statci 설정
        self.app.mount(
            "/static",
            StaticFiles(directory="/docker__WEBserver/static"),
            name="static",
        )
        
        
        
    def add_router(self):
        self.app_router = APIRouter()
        
        # 로그인
        self.app_router.get("/Login")(self.Login)

        # 통합 대시보드 
        self.app_router.get("/ALL_Dashboard")(self.ALL_Dashboard)

        # 특정 에이전트 페이지
        self.app_router.get("/Agent_Detail")(self.Agent_Detail)
        
        # 특정 에이전트, 특정 ROOT 프로세스 상세 페이지
        self.app_router.get("/Root_Process_Tree")(self.Root_Process_Tree)
        
        
        # LLM 분석 요청
        self.app_router.get("/LLM_Request")(self.LLM_Request)
        
        
        # WebSocket (챗봇 소켓)
        self.app_router.websocket("/ws")(self.ChatbotManager.WebSocket)
        
        # 라우터 추가
        self.app.include_router(self.app_router)
        
    # 로그인 (세션 얻는 과정)
    async def Login(self, request: Request):
        # 쿠키 체크
        if self.WebManager.cookie_manager.Check_Cookie(request=request):
            #return {"result":"success", "message":"이미 쿠키 존재"}
            return RedirectResponse(url="/ALL_Dashboard", status_code=302)

        # 리다이렉트 -> ALL_Dashboard로
        Response = RedirectResponse(url="/ALL_Dashboard", status_code=302)
        # 쿠키 설정
        self.WebManager.cookie_manager.Set_Cookie(Response)

        return Response
    
    # 대시보드
    async def ALL_Dashboard(self, request: Request):
        # 쿠키 체크
        if not self.WebManager.cookie_manager.Check_Cookie(request=request):
            return RedirectResponse(url="/Login", status_code=302)
        
        # 쿠키 조회
        cookie_value = self.WebManager.cookie_manager.Get_Cookie(request=request)
        
        # 에이전트 조회
        agents = self.EDR_Manager.Get_Agents()
        
        return self.Template.TemplateResponse(
            "dashboard.html",
            {
                "request":request,
                
                "agent_list": agents,
                
                'kibana_host': self.Kibana_host,
                'kibana_port': self.Kibana_port,
                
                "cookie": cookie_value,
                "websocket_connection_url": f"ws://{self.WebSocket_External_Host}:{self.WEB_port}/ws"
            }
        )
    
    # 대시보드 -> 에이전트 상세 페이지
    # 에이전트 상세 페이지
    async def Agent_Detail(self, request: Request, agent_id:str):
        # 쿠키 체크
        if not self.WebManager.cookie_manager.Check_Cookie(request=request):
            return RedirectResponse(url="/Login", status_code=302)
        
        # 쿠키 조회
        cookie_value = self.WebManager.cookie_manager.Get_Cookie(request=request)
        
        # 키바나 루시네 쿼리 
        lucene_result = self.EDR_Manager.KibanaAPI.Get_Iframe(lucene_query=f"categorical.Agent_Id : {agent_id} ")
        
        # [1/2] 특정 에이전트의 프로세스 정보 조회
        root_processes = self.EDR_Manager.Get_Processes(
            agent_id=agent_id,
        )
        
        return self.Template.TemplateResponse(
            "agent_detail.html",
            {
                "request":request,
                "query":lucene_result,
                "agent_id": agent_id,
                "root_processes": root_processes,
                
                'kibana_host': self.Kibana_host,
                'kibana_port': self.Kibana_port,
                
                "cookie": cookie_value,
                "websocket_connection_url": f"ws://{self.WebSocket_External_Host}:{self.WEB_port}/ws"

            }
        )
    
    # 대시보드 -> 특정 에이전트 -> 특정 ROOT 프로세스 트리 페이지
    async def Root_Process_Tree(self, request: Request, agent_id:str, root_process_id:str):
        # 쿠키 체크
        if not self.WebManager.cookie_manager.Check_Cookie(request=request):
            return RedirectResponse(url="/Login", status_code=302)
        
        # 쿠키 조회
        cookie_value = self.WebManager.cookie_manager.Get_Cookie(request=request)
        
        # 루시네 쿼리
        lucene_result = self.EDR_Manager.KibanaAPI.Get_Iframe(
            lucene_query=f"categorical.Agent_Id : {agent_id} AND categorical.process_info.Root_Parent_Process_Life_Cycle_Id : {root_process_id} "
        )
        
        # 루시네 쿼리 --> LLM TREE 연관분석 결과 대시보드 가져오기
        
        ## 1. SHA256가져오기 ( ROOT 프로세스가 가진 자신의 self_SHA256와 parent_SHA256 값가져오기 )
        self_sha256_by_ROOT_process = "" # 35f56e6019406ee4247dfaf7a96e210eee795c8b05dc3c3666a2f644a8d4beab
        parent_sha256_by_ROOT_process = "" # 6a33947b40670d815b3dc7d1435fb0b432beca371fd5e05e2e5190aef337df9b
        
        ## 2. -
        output  = self.EDR_Manager.ElasticsearchAPI.Query(
            query={
                "query" : {
                    "bool":{
                        "filter":[
                            {
                                "term":{
                                    "categorical.Agent_Id": agent_id
                                }
                            },
                            {
                                "term":{
                                    "categorical.process_info.Root_Parent_Process_Life_Cycle_Id": root_process_id
                                }
                            },
                            {
                                "exists":{
                                    "field":"unique.process_behavior_events.Process_Created"
                                }
                            }
                        ]
                    }
                },
                "size":1,
                "_source":{
                    "includes":[
                        "unique.process_behavior_events.Process_Created.ProcessSHA256", # self_SHA256
                        "unique.process_behavior_events.Process_Created.Parent_ProcessSHA256" # parent_SHA256
                    ]
                }
                
            },
            index="siem-edr-*",
            is_aggs=False
        )
        if len(output) > 0:
            
            self_sha256_by_ROOT_process = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["ProcessSHA256"]
            parent_sha256_by_ROOT_process = output[0]["_source"]["unique"]["process_behavior_events"]["Process_Created"]["Parent_ProcessSHA256"]
        
        print(f"self_sha256_by_ROOT_process -> {self_sha256_by_ROOT_process} // parent_sha256_by_ROOT_process -> {parent_sha256_by_ROOT_process}")
        ## 3. 루시네 쿼리 생성
        llm_query = self.EDR_Manager.KibanaAPI.Get_Iframe(
            lucene_query=f"edr.self_sha256 : {self_sha256_by_ROOT_process} AND edr.parent_sha256 : {parent_sha256_by_ROOT_process}"
        )
        # TREE 구하기
        process_tree, mermaid_graph = self.EDR_Manager.Get_Process_Tree(
            root_process_id=root_process_id # Root 프로세스 사이클 ID 
        )
        
        if (not process_tree) or (not mermaid_graph):
            return {"message": f'에이전트{agent_id} ==> {root_process_id} root 프로세스에 대한 이벤트 정보 및 tree가 없습니다.'}
        
        
        return self.Template.TemplateResponse(
            "Root_Process_Tree.html",
            {
                "request":request,
                "query":lucene_result,
                "llm_query": llm_query,
                "agent_id": agent_id,
                
                "root_process_cycle_id": root_process_id,
                "mermaid_code": mermaid_graph,
                
                'kibana_host': self.Kibana_host,
                'kibana_port': self.Kibana_port,
                
                "cookie": cookie_value,
                "websocket_connection_url": f"ws://{self.WebSocket_External_Host}:{self.WEB_port}/ws"
            }
        )
    
    # dict REUTNR (페이지가 아님)
    async def LLM_Request(self, request: Request, agent_id:str, root_process_id:str,):
        # 쿠키 체크
        if not self.WebManager.cookie_manager.Check_Cookie(request=request):
            return {"status": "fail", "message": "쿠키 체크 실패"}
        
        # 사전 중복 체크
        
        # 요청
        threading.Thread(
            target=self.BehaviorAnalzer.Thread_Tree_Analysis_Queue,
            args=(
                agent_id,
                root_process_id
            )
        ).start()
        
        return {"status":"success", "message":"요청-성공"}
        
        
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
        
    def run(self):
        uvicorn.run(self.app, host=self.WEB_host, port=self.WEB_port)
        

# Dockerfile 환경변수
import os


#<< 도커 적용시 풀것 >>
WEB_host = os.environ.get("WEB_HOST", "0.0.0.0")
WEB_port = os.environ.get("WEB_PORT", "8000")

elasticsearch_host = os.environ.get("ELASTICSEARCH_HOST", "0.0.0.0") # 기본값 도메인(호스트명) 이름
elasticsearch_port = os.environ.get("ELASTICSEARCH_PORT", "9200")

kibana_host = os.environ.get("KIBANA_HOST", "0.0.0.0") # 기본값 도메인(호스트명) 이름
kibana_port = os.environ.get("KIBANA_PORT", "5601")

core_server_host = os.environ.get("CORE_SERVER_HOST", "0.0.0.0") # 기본값 도메인(호스트명) 이름
core_server_port = os.environ.get("CORE_SERVER_PORT", "10000")

WebSocket_External_Host = os.environ.get("WEBSOCKET_EXTERNAL_HOST", "0.0.0.0") # WebSocket , Client 브라우저에 보여질 것 (무조건 설정해야함)

GOOGLE_GEMINI_API = os.environ.get("GOOGLE_GEMINI_API", " 구글 제미나이 API 키.. 필수키")

print(f"""
      
      [웹서버 환경변수 확인]
      WEB_HOST: {WEB_host}
      WEB_PORT: {WEB_port}
      
      ELASTICSEARCH_HOST: {elasticsearch_host}
      ELASTICSEARCH_PORT: {elasticsearch_port}
      
      KIBANA_HOST: {kibana_host}
      KIBANA_PORT: {kibana_port}
      
      CORE_SERVER_HOST: {core_server_host}
      CORE_SERVER_PORT: {core_server_port}
      
      WEBSOCKET_EXTERNAL_HOST: {WebSocket_External_Host}
      
      """)

t = WebServer(
    WEB_host=WEB_host,
    WEB_port=int(WEB_port),
    
    WebSocket_External_Host=WebSocket_External_Host,
    
    CoreServer_host=core_server_host,
    CoreServer_port=int(core_server_port),
    
    ElasticSearch_host=elasticsearch_host,
    ElasticSearch_port=int(elasticsearch_port),
    
    Kibana_host=kibana_host,
    Kibana_port=int(kibana_port),
)


# TEST
from BehaviorAnalyzerManagement.SigmaManagement.Sigma_Manager import Sigma_Manager, SigmaTargetEndpoint
t.BehaviorAnalzer.Start_Behavior_Analyzer(
    endpoint_type=SigmaTargetEndpoint.windows,
    agent_id="d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf",
    root_process_id="7ed54e018102a59f6ef14e7bbdf5f96112ac6b669e08b6ab65286a3d28eaf74693392d723fbc91672ba42c36ff26e71fc93dc819ecf4be70fe5ea3b8c8b35437"
)
# 6e603bf8b4f9e29e7b2fbced5c89d7d4fc641014db5e9460312e05602660710b01c289762031b0982228e496fff2b7f5089af049d409d4d9dec09eb84eec7193
'''from BehaviorAnalyzerManagement.SigmaManagement.Sigma_Manager import Sigma_Manager, SigmaTargetEndpoint
t.Sigma_Manager.Sigma_Analysis(
    target=SigmaTargetEndpoint.windows,
    agent_id="d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf",
    root_process_id="7156ea5741c56fe0c0e725d0ef53bd199766ce60df2218d9bdaa4e05bfaa8ef2420da070c1bc228f89c456e9915979fb4dc99021f7f6e9c1fc3c3be98f7e4697",

)'''

#t.EDR_Manager.Get_Processes(agent_id="d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf")


# TEST CODE   

'''tree, graph = t.EDR_Manager.Get_Process_Tree(
    root_process_id="7156ea5741c56fe0c0e725d0ef53bd199766ce60df2218d9bdaa4e05bfaa8ef2420da070c1bc228f89c456e9915979fb4dc99021f7f6e9c1fc3c3be98f7e4697"
)

print(tree)
'''

# Win 태블릿 -> 에이전트 ID  94cc91fbe1cc241c3de1fd8bea909febffee363cd6028195a04718e5098d634f9156bbc395e690e0c7c3c4194da29082d408b7cd44e154aeee21d147682957b1

t.run()