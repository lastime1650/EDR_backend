# 챗봇의 AGENT 도구를 정의하고 반환하는 클래스
import asyncio
import json
import threading
from typing import List, Optional

from langchain_core.tools import Tool

# 중간에 웹 소켓 클라이언트에게 전송할 수 있음
from Chatbot.WebSocketManager import WebSocketManager

from EDR.EDRManager import EDR_Manager

from Utility.timestamper import Get_Current_Time

class Chatbot_tools():
    def __init__(self,  websocket_manager:WebSocketManager, EDR_Manager:EDR_Manager):
        self.websocket_manager = websocket_manager
        self.EDR_Manager = EDR_Manager # 코어 서버 접근 관리
        pass

    # 실제 도구 메서드
    # 현재 등록된 에이전트 목록 가져오기
    def Get_All_Agents(self, From_LLM: str) -> str:

        # ElasticSearch 객체를 통하여 에이전트 목록을 가져온다.

        # 결과 반환
        return json.dumps({
            "agents": self.EDR_Manager.Get_Agents() # 코어 서버 에이전트 목록 가져오기
        }, ensure_ascii=False)

    # 현재 리다이렉트 가능한 페이지 목록 가져오기
    def Get_All_Pages(self, From_LLM: str) -> str:
        return json.dumps([
            {
                "page_name": "/ALL_Dashboard",
                "page_description": "현재 EDR에 연결된 모든 에이전트로부터 수집된 종합 이벤트 정보를 반환하는 페이지이다. (실제 GUI에서는 ElasticSearch정보를 기반한 키바나 대시보드이며, 모든 에이전트로부터 수집한 데이터와 에이전트 목록이 노출된다.)",
                "needed_parameters": []
            },
            {
                "page_name": "/Agent_Detail",
                "page_description": "현재 EDR에 연결된 모든 에이전트 중에 특정된 하나의 에이전트에 대한 대시보드 페이지이다.",
                "needed_parameters": [{
                    "parameter_name": "agent_id",
                    "description": "에이전트 ID",
                    "example": "/Agent_Detail?agent_id=d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf"
                }]
            },
            {
                "page_name": "/Root_Process_Tree",
                "page_description": "현재 EDR에 연결된 특정 에이전트에 대한 특정 루트 프로세스를 Tree구조로 보여주는 페이지이다.",
                "needed_parameters": [
                    {
                        "parameter_name": "agent_id",
                        "description": "에이전트 ID",
                    },
                    {
                        "parameter_name": "root_process_id",
                        "description": "루트 프로세스 ID",
                    },
                    {
                        "example": "/Root_Process_Tree?agent_id=d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf&root_process_id=659f83b7e8b18e976e6f03ce8f1079bb5cbdb29c11ac4ec071a2ecc531e4301ecea92d2a90b0e881ec15124d360654c47aac2657fbaffa5ce180813d06c675e4"
                    }
                ]
            }
        ], ensure_ascii=False
        )

    def Get_ALL_Root_Process_ID_by_Specific_Agent(self, From_LLM: str) -> str:
        parsed = self.LLM_to_JSON(From_LLM)
        if not parsed:
            return self.output_JSON_Parsing_failure()

        agent_id:Optional[str] = parsed["agent_id"]

        return json.dumps(
            self.siem_manager.EDR.Get_Root_Processes(agent_id),
            ensure_ascii=False
        )

    def redirect_page(self, From_LLM: str) -> str:
        parsed = self.LLM_to_JSON(From_LLM)
        if not parsed:
            return self.output_JSON_Parsing_failure()

        # 페이지 리다이렉트
        page_name = parsed['page_name']
        cookie = parsed['cookie']

        if len(cookie) == 0:
            return "cookie값이 공란입니다. 다시 cookie값을 지정해주세요."
        if len(page_name) == 0:
            return "페이지 이름이 공란입니다. 다시 페이지 이름을 지정해주세요."

        if page_name is None or cookie is None:
            return "잘못된 페이지 리다이렉트 요청입니다.-> False"

        redirect_command_json = {
            "cmd": "WEB_redirect_the_page",
            "data": page_name
        }

        # 웹 소켓 클라이언트에게 전송 ( 코루틴 이므로,코루틴 처리 메서드를 사용하여 비동기 함수에서 알아서 처리 하도록 한다)
        # 코루틴 객체 생성
        corutine_object = self.websocket_manager.Send_msg(

            cookie,
            json.dumps(
                redirect_command_json,
                ensure_ascii=False
            )
        )

        # 다른 스레드에서 코루틴 처리
        threading.Thread(
            target=self.websocket_manager.Run_Async_corutine_object_,
            args=(corutine_object,) # 코루틴 객체 인자전달
        ).start()

        return f"이동 요청 완료"

    # EDR내 전체 에이전트 이벤트 탐색
    def search_edr_event_info(self, From_LLM: str) -> str:
        parsed = self.LLM_to_JSON(From_LLM)
        if not parsed:
            return self.output_JSON_Parsing_failure()

        agent_id:Optional[str] = parsed["options"]['agent_id'] if 'agent_id' in parsed["options"] else None
        root_process_id:Optional[str] = parsed["options"]['root_parent_process_life_cycle_id'] if 'root_parent_process_life_cycle_id' in parsed["options"] else None
        process_life_cycle_id:Optional[str] = parsed["options"]['process_life_cycle_id'] if 'process_life_cycle_id' in parsed["options"] else None
        query_string:Optional[str] = parsed["options"]['query_string'] if 'query_string' in parsed["options"] else None

        hours:Optional[int] = parsed['hours'] if 'hours' in parsed else None

        cmds:List[str] = parsed['cmd']

        output: List[dict] = []

        if len(cmds) == 0:
            return "cmd 목록이 없습니다. 다시 입력해주세요."
        else:
            for cmd in cmds:
                if cmd == "ALL_DASHBOARD":
                    output.append(
                        {
                            "cmd": "ALL_EVENTS",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.ALL_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                elif "REGISTRY" in cmd:
                    output.append(
                        {
                            "cmd": "REGISTRY",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.REGISTRY_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                elif "FILESYSTEM" in cmd:
                    output.append(
                        {
                            "cmd": "FILESYSTEM",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.FILESYSTEM_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                elif "NETWORK" in cmd:
                    output.append(
                        {
                            "cmd": "NETWORK",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.NETWORK_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                elif "PROCESS" in cmd:
                    output.append(
                        {
                            "cmd": "PROCESS",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.PROCESS_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                elif "IMAGELOAD" in cmd:
                    output.append(
                        {
                            "cmd": "IMAGELOAD",
                            "agent_id": agent_id,
                            "root_process_id": root_process_id,
                            "process_life_cycle_id": process_life_cycle_id,
                            "result": self.EDR_Manager.KibanaAPI.SearchDashboard.IMAGELOAD_DASHBOARD(
                                agent_id=agent_id,
                                Root_Parent_Process_Life_Cycle_Id=root_process_id,
                                Process_Life_Cycle_id=process_life_cycle_id,
                                query_string=query_string,
                                Hours=hours
                            )
                        }
                    )
                else:
                    return "잘못된 cmd 명칭입니다. 다시 입력해주세요."

        return json.dumps(output,ensure_ascii=False)

    def response(self, From_LLM: str) -> any:
        parsed = self.LLM_to_JSON(From_LLM)
        if not parsed:
            return self.output_JSON_Parsing_failure()
        # 차단 -response
        # 필드 검사
        if "cmd" not in parsed:
            return "cmd 필드가 없습니다. 예를 들어 'cmd' 를 입력해주세요."
        if "agent_id" not in parsed:
            return "agent_id 필드가 없습니다. 예를 들어 'agent_id' 를 입력해주세요."

        cmd = parsed["cmd"]
        agent_id = parsed["agent_id"]
        is_remove = bool(parsed["is_remove"])

        if cmd == "process":
            return self.EDR_Manager.CoreServerAPI.CoreServer_agent_response_process(
                agent_id=agent_id,
                sha256=parsed["info"]["sha256"],
                file_size=parsed["info"]["file_size"],
                is_remove=is_remove
            )
        elif cmd == "file":
            return self.EDR_Manager.CoreServerAPI.CoreServer_agent_response_file(
                agent_id=agent_id,
                sha256=parsed["info"]["sha256"],
                file_size=parsed["info"]["file_size"],
                is_remove=is_remove
            )
        elif cmd == "network":
            return self.EDR_Manager.CoreServerAPI.CoreServer_agent_response_network(
                agent_id=agent_id,
                remoteip=parsed["info"]["remoteip"],
                is_remove=is_remove
            )
        else:
            return "잘못된 cmd 명칭입니다. 다음과 같이 명령을 입력해주세요. cmd 명령은 'process', 'file', 'network'입니다."

    def get_current_time(self, From_LLM: str) -> str:
        parsed = self.LLM_to_JSON(From_LLM)
        if not parsed:
            return self.output_JSON_Parsing_failure()

        return json.dumps(
            {
                "현재 시간": Get_Current_Time()
            },
            ensure_ascii=False
        )

    # 에이전트-함수 내장 메서드
    def LLM_to_JSON(self, input: str) -> Optional[dict]:
        import json

        result: Optional[dict] = None
        try:
            result = json.loads(input.replace("```json", "").replace("```", "").replace("\n", ""))
        except:
            return None

        return result

    def output_JSON_Parsing_failure(self) -> str:
        return "잘못된 JSON입니다. 다시 입력해주세요."

    # Tool 반환
    def Output_Tools(self)->List[Tool]:
        tools:List[Tool] = []

        # 에이전트 목록 가져오기
        tools.append(
            Tool(
                name="search-all-agent-info",
                func=self.Get_All_Agents,
                description="""
                        ** [함수 설명]
                        1. 현재 에이전트 목록을 가져옵니다.
                        2. 에이전트 상태를 알 수 있습니다.

                        ** [함수 사용 조건]
                        1. 에이전트 목록이 필요할 때 호출합니다.

                        ** [함수 인자]
                        1. 온전한 JSON형식으로 입력해야합니다.
                        ```json
                        {
                            "cmd": "Get_All_Agents",
                        }
                        ```

                        ** [함수 반환값]
                        1. 이 함수는 에이전트 목록을 반환합니다. 반환 형식은 JSON 형식이지만, 아닐 수 있습니다.
                        2. 에이전트 목록은 아래와 같이 구성될 수 있습니다.
                        ```json
                        {
                            "agents":
                                [ㄱ
                                    {
                                        "agent_id": "d7dbf53c4007173122ff65cbba4a1cf103277eb91f3c366a534ed37a942e363cdd7367ef18dc11d0386b84797a660c558f3b76fa97e2b497928b2b61f73fdccf", 
                                        "status": true, // -> ( true 면 현재 에이전트가 연결되어 있음, false 면 연결되어 있지 않음 )
                                        "os": "Windows(x64) 10.0.22631.276.2" // -> 윈도우 운영체제
                                    }
                                ]
                        }
                        ```

                        """
            )
        )

        '''# 특정 에이전트의 Root 프로세스 ID 목록 가져오기
        tools.append(
            Tool(
                name="search-all-root_process_id-by-specific-agent-info",
                func=self.Get_ALL_Root_Process_ID_by_Specific_Agent,
                description="""
                                ** [함수 설명]
                                1. 특정된 에이전트에서 수집된 Root 프로세스 ID값을 가져옵니다.
                                2. 특정된 에이전트에서 수집된 Root 프로세스 ID를 알 수 있습니다.

                                ** [함수 사용 조건]
                                1. 특정 에이전트 ID를 통해서 Root 프로세스 ID를 알 수 있습니다. 

                                ** [함수 인자]
                                1. 온전한 JSON형식으로 입력해야합니다.
                                ```json
                                {
                                    "agent_id": "EDR에 연결된 에이전트 ID"
                                }
                                ```

                                ** [함수 반환값]
                                1. 이 함수는 프로세스 Tree의 상위 프로세스인 Root 프로세스 ID에 대한 목록을 반환합니다. 반환 형식은 JSON 형식이지만, 아닐 수 있습니다.


                                """
            )
        )'''

        # 리다이렉트 가능한 페이지 목록 가져오기
        tools.append(
            Tool(
                name="Get_All_Pages",
                func=self.Get_All_Pages,
                description='''
                        ** [함수 설명]
                        1. 당신이 리다이렉트 할 수 있는 모든 페이지 정보를 가져올 수 있습니다.

                        ** [함수 사용 조건]
                        1. 당신이 리다이렉트를 하기 전에, 가능한 페이지이거나, 사용자에게 페이지 리다이렉트에 필요한 페이지 인지 확인할 때 사용합니다.

                        ** [함수 인자]
                        1. 온전한 JSON형식으로 입력해야합니다.
                        ```json
                        {
                            "cmd": "Get_All_Pages",
                        }
                        ```

                        ** [함수 호출 후 반환 형식]
                        이 도구의 반환 값의 예시는 다음과 같습니다.
                        List[Dict] 타입으로 리다이렉트 가능한 페이지를 제공합니다.
                        [
                            {
                                "page_name": "/ALL_Dashboard", // 페이지 이름(/ 붙여서) .
                                "page_description": "현재 EDR에 수집된 종합 정보를 반환하는 페이지.....", //해당 페이지에 대한 설명으로 리다이렉트 할 대상 페이지에 대한 설명을 참고할 수 있음
                                "needed_parameters" : [] // 해당 페이지에 필요한 인자 이름과 설명 (공란 [] 인 경우는 필요없음을 의미함 )
                            },,,,,
                        ]
                        '''
            )
        )


        # 현재 페이지(사용자가 현재 위치한 페이지) 정보 가져오기
        # 리다이렉트 하기
        tools.append(
            Tool(
                name="redirect_page",
                func=self.redirect_page,
                description='''
                        ** [함수 설명]
                        1. 현재 에이전트를 사용하는 페이지를 강제 리다이렉트하는 함수/도구 입니다.
                        2. 리다이렉트 가능한 모든 페이지 리스트를 보려면 'Get_All_Pages' 도구를 사전에 사용하는 것을 추천합니다.
                        

                        ** [함수 사용 조건]
                        1. 사용자가 현재 위치한 페이지를 다른 페이지로 이동 시키려고 할 때 사용합니다. ( 정확한 판단이 되지 않으면, 사용자에게 이동할 지 여부를 물어보세요 )

                        ** [함수 인자]
                        1. 다음과 같은 온전한 JSON 형식 인자로 입력합니다.
                        ```json
                        {
                            "cookie": "사용자 요청 JSON에서 cookie값을 그대로 지정해야합니다.(이유: 사용자 개별적 요청 처리 로직)",
                            "page_name": "/ALL_Dashboard", // 이동할 페이지 이름( 맨앞 슬래시는 필수입니다. ) 페이지 리스트는 [Get_All_Pages] 도구를 사전에 호출하여 알 수 있습니다. 하지만, 파라미터가 필요한 페이지는 파라미터를 포함해야합니다(Get_All_Pages도구의 반환값에서 리다이렉트할 페이지의 'needed_parameters'를 보고 정확한 파라미터명으로 값을 넣어 완성하세요.) . 별도의 파라미터가 존재하는 경우 파라미터와 그것을 담는 실제 값까지 포함하여 지정해야합니다. 예시-> "/Agent_Detail?agent_id=d7db..."
                        }
                        ```
                        2. "cookie" 키 값은 필수 입니다. (사용자 요청 JSON에서 그대로 cookie값을 사용합니다.)
                        3. "page_name" 키 값은 필수 입니다. (이동할 페이지)

                        ** [함수 호출 후 반환 형식]
                        처리완료 응답을 합니다.
                        '''
            )
        )
        # 특정 에이전트의 특정 ROot 프로세스 정보 확인
        # 특정 에이전트의 특정 Root 프로세스 정보의 특정 프로세스 인스턴스 확인
        # 특정 에이전트에 차단

        #--
        tools.append(
            Tool(
                name="get_current_time",
                func=self.get_current_time,
                description='''
                            ** [함수 설명]
                            1. 현재 시간을 가져옵니다.
                            
                            ** [함수 사용 조건]
                            1. 이 함수는 현재 시간을 가져옵니다.
                            
                            ** [함수 인자]
                            0. 온전한 JSON형식으로 입력해야합니다.
                            ```json
                            {
                                "cmd": "get_current_time"
                            }
                            ```
                            
                            ** [함수 반환값]
                            1. 이 함수는 현재 시간을 ISO 형식으로 마지막 3자리 밀리초까지 포함하여가져옵니다. 이는 EDR에서 사용하는 시간 규격이기 때문입니다.
                            사용자에게 직접 노출해야하는 시간인 경우, 이해할 수 있도록 자연어 처리하여 시간을 사용자에게 알려야합니다.
                            분석에서는 ISO형식을 사용합니다.
                            
                            '''
            )
        )

        # 이벤트 탐색기
        tools.append(
            Tool(
                name="search-edr-agent-event-info",
                func=self.search_edr_event_info,
                description='''
                            ** [함수 설명]
                            1. EDR에 연결된 에이전트들이 수집한 이벤트 현황을 다양하게 탐색할 때 호출할 수 있습니다. 
                            2. 또는 사용자가 현재 속한 특정 페이지에 대한 이벤트 목록을 가져오기 위해 이 도구를 호출할 수 있습니다. 
                            3. [ALL_DASHBOARD] 페이지는 {특정되지 않음 모든 에이전트}에 대한 이벤트를 이 도구를 사용하여 탐색결과를 가시화합니다. 
                            4. [Agent_Detail] 페이지는 {특정된 에이전트}에 대한 {행위들-> registry, filesystem, network, process, imageload}이벤트를 이 도구를 사용하여 탐색결과를 가시화합니다. 
                            5. [ROOT_Process_Detail] 페이지는 {특정된 에이전트} -> {특정된 루트 프로세스}에 대한 {행위들-> registry, filesystem, network, process, imageload}이벤트를 이 도구를 사용하여 탐색결과를 가시화합니다.

                            ** [함수 사용 조건]
                            1. EDR에 연결된 모든 에이전트가 수집한 이벤트 정보가 필요할 때 사용합니다.
                            2. [ALL_DASHBOARD] 페이지가 현재 어떠한 이벤트 정보를 노출시키는 지 확인하기 위해 호출할 수 있습니다.

                            ** [함수 인자]
                            0. cmd 목록은 다음과 같이 정의되어 있습니다.
                            - cmd
                            -- "ALL_DASHBOARD" // EDR 전체 수집 대시보드
                            -- "REGISTRY_DASHBOARD" // 레지스트리 수집 대시보드
                            -- "FILESYSTEM_DASHBOARD" // 파일시스템 수집 대시보드
                            -- "NETWORK_DASHBOARD" // 네트워크 수집 대시보드
                            -- "PROCESS_DASHBOARD" // 프로세스 수집 대시보드
                            -- "IMAGELOAD_DASHBOARD" // 이미지 로드 수집 대시보드
                            
                            1. 다음과 같은 온전한 JSON 형식 인자로 입력합니다.
                            ```json
                            {
                                "cmd": List[str]형식, [상기 설명된 cmd 목록 1개 이상 사용], // 예시 방법-> ["ALL_DASHBOARD"] 또는 ["ALL_DASHBOARD", "FILESYSTEM_DASHBOARD",,,] 목적에 따라 설정하세요.
                                "hours": 12 // [Hours]기준; 현재시간을 기준으로 범위를 [시간]기준으로 설정합니다. 예를 들어, 12으로 설정한다면 ,, 12시간을 설정하며 이전 12시간부터 지금 이후의 12 시간 후까지 발생한 이벤트를 한정하여 행위를 확인할 수 있습니다. 
                                "options": { // 설정 옵션 정보 ( 아예 설정할 게 없는 경우 {} 으로 공란 )
                                    "agent_id": "EDR에 연결된 에이전트 ID" // 이벤트 수집에 특정 {에이전트 ID} 필터링을 위해 사용합니다.
                                    "root_parent_process_life_cycle_id": "sha512 값..." // 프로세스 Root 사이클 ID값으로 특정 프로세스 TREE에 묶인 모든 프로세스 대한 행위 목록을 조회할 때 사용합니다.
                                    "process_life_cycle_id": "sha512 값..." // 특정 프로세스 하나에 대한 행위 목록을 조회할 때 사용합니다. (참고로 이 지정된 프로세스 id는 어느 특정 root 프로세스 트리구조에 속한 하나의 프로세스입니다.)
                                    "query_string": "쿼리 문자열" // ElasticSearch의 'query_string' 쿼리 필드 값을 지정합니다. 이 쿼리를 사용하여 이벤트를 필터링할 때 사용합니다. -> 프로세스 이름으로 특정 검색할 때나 사용됩니다. 이때 예시로, *{사용자가 요구한 문자열이나 키워드값}* ->  전체 검색이 가능하도록 양옆으로 별 특수문자를 추가하십시오.(기본) 유연하게 사용자 요구를 기반으로 지정해야합니다. 
                                }
                            }
                            ```
                            2. 'cmd' 키는 필수적인 key입니다.
                            3. 'hours' 키는    필수적인 key입니다.
                            4. 'options' 키는 필수적인 key입니다.
                            5. 'agent_id' 키는 선택적인 key입니다.
                            6. 'root_parent_process_life_cycle_id' 키는 선택적인 key입니다.
                            7. 'process_life_cycle_id' 키는 선택적인 key입니다.
                            8. 'query_string' 키는 선택적인 key입니다.
                            
                            
                            
                            ** [함수 호출 후 반환 형식]
                            응답은 List[Dict] JSON형식으로 반환됩니다.
                            이 결과를 통해 바로 사용자에게 반환하려는 경우, 이쁘게 정리하여 연관분석시 정확히 활용하기 위해 자세하게 리포트 형태로 반환하십시오.
                            예를 들어 각각의 DASHBOARD에는 개별적으로 자신의 행위에 따라 수집한 수치가 있습니다. 
                            처음에는 전체적으로 파악하지 않고, List내 요소를 하나씩 파악(타임라인기반으로 doc_count인 경우 그 빈도수나 발생한 경로등을 파악할 수 있음)한 후 모두 전체적으로 수집해야하는 전략으로 해야합니다.
                            인자 입력시 요청한 agent_id, root_process_id, process_life_cycle_id값의 일관성을 지켜 그대로 그 응답을 반환하세요.
                            중간에 틀린 값으로 응답하여 큰 손실이 발생한 적이 있으며, 이런 일들이 없도록 합니다.
                        
                        '''
            )
        )

        # 이벤트 탐색기
        tools.append(
            Tool(
                name="response",
                func=self.response,
                description='''
                                ** [함수 설명]
                                1. EDR에 연결된 에이전트들에 "차단"을 "등록"하거나 "해제"하는 함수.

                                ** [함수 사용 조건]
                                1. 사용자 입력에서 "특정 에이전트 ID"가 지정되어 있을 때 호출 가능
                                2. 사용자 입력에서 다음과 같은 정보가 포함되었을 때 호출가능.
                                
                                << 차단 및 해제가능한 유형 >>
                                1. 파일 차단  및 해제
                                2. 프로세스 차단  및 해제
                                3. 네트워크 차단 및 해제
                                총 3가지이다.
                                
                                [1]:파일 차단 및 해제의 경우 사용자로부터 다음과 같은 문장을 받아야한다.
                                1. 파일 SHA256값
                                2. 파일 크기
                                +. 에이전트 ID 
                                
                                [2]:프로세스 차단 및 해제의 경우 사용자로부터 다음과 같은 문장을 받아야한다.
                                1. 파일 SHA256값
                                2. 파일 크기
                                +. 에이전트 ID 
                                
                                [3]:네트워크 차단 및 해제의 경우 사용자로부터 다음과 같은 문장을 받아야한다.
                                1. remoteip, 원격지 IP
                                +. 에이전트 ID 
                                
                                * 만약 하나씩 사용자가 전달할 수 있는 경우에 대비하여야한다. 이 경우, 하나씩 물어가보면서 정보를 완성해야한다.
                                
                                
                                ** [함수 인자]
                                0. cmd 목록은 다음과 같이 정의되어 있습니다.
                                - cmd
                                -- "process" 명령은 프로세스 차단  및 해제 명령을 설정합니다.
                                -- "file" 명령은 파일 차단  및 해제 명령을 설정합니다.
                                -- "network" 명령은 네트워크 차단  및 해제 명령을 설정합니다.

                                1. 다음과 같은 온전한 JSON 형식 인자로 입력합니다.
                                ```json
                                {
                                    "cmd": str형식 "process"라면 프로세스 차단 및 해제 명령을 설정하고, "file"라면 파일 차단 및 해제 명령을 설정하고, "network"라면 네트워크 차단 및 해제 명령을 설정하라.,
                                    "agent_id": "EDR에 연결된 에이전트 ID",
                                    "is_remove": bool형식 True이면 차단해제, False이면 차단등록 // 정확하게 설정해야합니다 (엄청 민감한 필드임)
                                    "info": {
                                        // "cmd" 지정된 값에 따라 아래 필드를 적절히 입력하시오.
                                        "SHA256": "SHA256값",
                                        "FILE_SIZE": 1024,
                                        "remoteip": "8.8.8.8",
                                    }
                                    
                                }
                                ```
                                0. 'is_remove' 키는 필수적이며, 차단 또는 해제를 설정하는 신중한 key입니다.
                                1. 'cmd' 키는 필수적인 key입니다.
                                2. 'info' 키는    필수적인 key입니다.
                                3. 'agent_id' 키는 필수적인 key입니다.
                                4. 나머지 키는 cmd에 따라 설정되는 key입니다.



                                ** [함수 호출 후 반환 형식]
                                응답은 List[Dict] JSON형식으로 반환됩니다.
                                이 결과를 통해 바로 사용자에게 반환하려는 경우, 이쁘게 정리하여 연관분석시 정확히 활용하기 위해 자세하게 리포트 형태로 반환하십시오.
                            '''
            )
        )

        return tools

