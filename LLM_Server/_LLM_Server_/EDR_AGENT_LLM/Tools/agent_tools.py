import json
from typing import List, Optional

import requests
from langchain_core.tools import Tool

# WebSocket 관리 모듈
from _EDR_WebServer_.WebSocket_management.WebSocket_Manager import WebSocketManager
from _LLM_Server_.EDR_LLM_EVAL.LLM_EVAL.Share_Conversation_Memory.Share_converstaion_mem import Share_ConversationMemory


class Agent_tools():
    def __init__(self, core_server_ip:str, core_server_port:int, WebSocket_Manager:WebSocketManager):
        self.main_core_server_url = f"http://{core_server_ip}:{core_server_port}"
        self.WebSocket_Manager = WebSocket_Manager

        pass

    # 모든 에이전트에 대한 데이터 요청
    def GET_ALL_Agent_Data(self, llm_input:str)->str:
        req_url = f"{self.main_core_server_url}/api/GET/agent"
        req_data = {
            "is_detail_mode": False
        }
        return str(self._requests_POST(req_url, req_data))

    # 특정 에이전트에 대한 데이터 요청
    def GET_Specific_Agent_Data(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, ["agent_id"])
        if not output:
            return "잘못된 JSON입니다. 다시 올바르게 입력하시고, 맨 양 옆은 { 와 } 으로 묶어야 JSON 인식됩니다. 예를 들어,  \"`{ 및 }`\" 는 인식되지 않습니다."
        req_url = f"{self.main_core_server_url}/api/GET/agent/specific"
        req_data = {
            "agent_id": output["agent_id"],
            "is_detail_mode": False
        }
        return str(self._requests_POST(req_url, req_data))

    # 프로세스 인스턴스 요청
    def GET_Instance_Data(self, llm_input:str)->str:
        '''


        이거 로직 바꿔야함


        :param llm_input:
        :return:
        '''
        output = self._is_valid_parm(llm_input, ["agent_id","instance_id"])
        if not output:
            return "잘못된 JSON입니다. 다시 올바르게 입력하시고, 맨 양 옆은 { 와 } 으로 묶어야 JSON 인식됩니다. 예를 들어, \"`{ 및 }`\" 는 인식되지 않습니다."

        req_url = f"{self.main_core_server_url}/api/GET/agent/instance"
        req_data = {
            "agent_id": output["agent_id"],
            "instance_id": output["instance_id"]
        }
        return str(self._requests_POST(req_url, req_data))

    # 정책에 대한 데이터 요청
    def GET_Policy_Data(self, llm_input:str)->str:

        req_url = f"{self.main_core_server_url}/api/GET/policy"
        req_data = {}
        return str(self._requests_POST(req_url, req_data))

    # 페이지 분석
    def analysis_page(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input)
        if "sub_dir" not in output:
            return "sub_dir키가 없습니다. 예를 들어 '/Agents', 'Agent_Detail', 'Instance_Detail' 등을 입력해주세요."
        if "parameters" not in output:
            return "parameters키가 없습니다. 이 키의 값의 형식은 파라미터 당 json 형식으로 입력해야합니다."

        if "agents" in str(output["sub_dir"]).lower():
            req_url = f"{self.main_core_server_url}/api/GET/agent"
            req_data = {
                "is_detail_mode": False
            }
            return f"당신이 전달한 분석요청 {output['sub_dir']}에 대해 가져온 JSON반환 값: {str(self._requests_POST(req_url, req_data))}"

        elif "agent_detail" in str(output["sub_dir"]).lower():
            req_url = f"{self.main_core_server_url}/api/GET/agent/specific"
            req_data = {
                "agent_id": output["parameters"]["agent_id"],
            }
            return f"당신이 전달한 분석요청 {output['sub_dir']}에 대해 가져온 JSON반환 값: {str(self._requests_POST(req_url, req_data))}"

        elif "instance_detail" in str(output["sub_dir"]).lower():
            req_url = f"{self.main_core_server_url}/api/GET/agent/instance"
            req_data = {
                "agent_id": output["parameters"]["agent_id"],
                "instance_id": output["parameters"]["instance_id"]
            }
            return f"당신이 전달한 분석요청 {output['sub_dir']}에 대해 가져온 JSON반환 값: {str(self._requests_POST(req_url, req_data))}"

        else:
            return "해당 sub_dir값은 지원하지 않습니다. 즉, 지원하지 않기에 분석이 불가능합니다."

    #-------

    # 차단
    def SET_response_block(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, ["response_type","agent_id"])
        if not output:
            return "당신은 인수를 올바를게 설정하지 않았습니다."

        # 1. 먼저 에이전트로부터 현재 등록된 차단 정보를 모두 가져오도록 하고, 동일한 것이 있는지 확인한다.
        rq_url = f"{self.main_core_server_url}/api/GET/response"
        rq_data = {
            "agent_id": output["agent_id"]
        }
        registered_blocks = self._requests_POST(rq_url,rq_data)
        if registered_blocks:
            for block_info in registered_blocks["message"]["infos"]:
                if output["response_type"] == "network":
                    if block_info["remoteip"] == output["remoteip"]:
                        return "이미 차단한 IP가 존재합니다. 중복이 되어선 안되므로 등록이 실패됩니다."

                elif output["response_type"] == "process":
                    if block_info["sha256"] == output["sha256"] and block_info["file_size"] == output["file_size"]:
                        return "이미 차단한 프로세스가 존재합니다. 중복이 되어선 안되므로 등록이 실패됩니다."

                elif output["response_type"] == "file":
                    if block_info["sha256"] == output["sha256"] and block_info["file_size"] == output["file_size"]:
                        return "이미 차단한 파일이 존재합니다. 중복이 되어선 안되므로 등록이 실패됩니다."


        req_url = f"{self.main_core_server_url}/api/SET/response"

        if output["response_type"] == "network":
            req_data = {
                "cmd": 10720, # Response_Network
                "agent_id": output["agent_id"],
                "remoteip": output["remoteip"]
            }
        elif output["response_type"] == "process":
            req_data = {
                "cmd": 10710,  # Response_Process
                "agent_id": output["agent_id"],

                "sha256": output["sha256"],
                "file_size": output["file_size"]
            }
        elif output["response_type"] == "file":
            req_data = {
                "cmd": 10730,  # Response_File
                "agent_id": output["agent_id"],

                "sha256": output["sha256"],
                "file_size": output["file_size"]
            }
        else:
            return "해당 response_type값은 지원하지 않습니다(대소문자 구별됨). 즉, 지원하지 않기에 차단 요청이 불가능합니다."

        return str(self._requests_POST(req_url, req_data))

    def GET_response(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, ["agent_id"])
        if not output:
            return "당신은 인수를 올바를게 설정하지 않았습니다."

        # 1. 먼저 에이전트로부터 현재 등록된 차단 정보를 모두 가져오도록 하고, 동일한 것이 있는지 확인한다.
        rq_url = f"{self.main_core_server_url}/api/GET/response"
        rq_data = {
            "agent_id": output["agent_id"]
        }
        registered_blocks = self._requests_POST(rq_url, rq_data)
        return f'{registered_blocks["message"]["infos"]}'

    #-- 유틸리티

    # requests 실행
    def _requests_POST(self, url:str, data:Optional[dict]=None)->Optional[dict]:
        headers = {"Content-Type": "application/octet-stream"}
        try:
            if data:
                response = requests.post(
                    url,
                    headers=headers,
                    data=json.dumps(data)
                )
            else:
                response = requests.post(
                    url,
                    headers=headers
                )

            return dict( response.json() )
        except:
            return None

    # LLM 에이전트가 설정한 파라미터가 목표에 올바른지 체크
    def _is_valid_parm(self, parm:str, input_keys:Optional[List]=None)->Optional[dict]:
        output:Optional[dict] = None
        try:
            output = json.loads( parm.replace("```json","").replace("```","").replace("\n","").replace("``","").replace("`","") )
            if input_keys:
                for key in output:
                    if key not in input_keys:
                        return None
            return output

        except:
            return output

    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    # [웹 페이지 관련 Tool]

    # 웹 페이지 리다이렉트 함수
    def WEB_redirect_page(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, None)
        if not output:
            return "잘못된 JSON입니다. 다시 올바르게 입력하세요."

        # 파라미터 추출하여 하나의 url로 생성
        url = f"{output['sub_web_dir']}?"
        for key in output["arguments"]:
            url += f"{key}={output['arguments'][key]}&"

        send_json = {
            "cmd": "WEB_redirect_the_page",
            "data": url
        }
        #await self.WebSocket_Manager.Get_WebSocket_instance(output["SESSION_ID"]).send_json(send_json)
        return f"{json.dumps(send_json, ensure_ascii=False)} 이대로 Final Answer 하세요 "

    # 웹 페이지 자가 생성 함수
    def WEB_create_html_code_page(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, None)
        if not output:
            return "잘못된 JSON입니다. 다시 올바르게 입력하세요."

        cmd = "WEB_create_html_for_a_user"
        SESSION_ID = output["SESSION_ID"]
        HTML_CODE = output["HTML_CODE"]

        return json.dumps({"cmd": cmd, "data": HTML_CODE},ensure_ascii=False)

    # 특정 인스턴스 분석 함수
    def WEB_instance_analysis(self, llm_input:str)->str:
        output = self._is_valid_parm(llm_input, ["Instance_id"])
        if not output:
            return "잘못된 JSON입니다. 다시 올바르게 입력하세요."

        MemoryConversationBuff =  Share_ConversationMemory().Get_Conversation(ConversationID=output["Instance_id"], is_from_hdd=True)
        if MemoryConversationBuff:
            output = {
                "result": []
            }
            '''
            "a" : [
                {
                    "EDR": "분석을 위해 요청한 데이터", // 타입이 str 또는 JSON일 수 있습니다.
                    "LLM": "요청한 데이터에 대한 LLM 분석 결과" // 타입이 str 또는 JSON일 수 있습니다.
                },,,,,,, ++ 
            ]
            '''
            it = iter(MemoryConversationBuff.chat_memory.messages)
            for message in it:
                output["result"].append(
                    {
                        "EDR": message.content,
                        "LLM": next(it).content
                    }
                )
            return "해당 인스턴스에 대한 LLM 결과가 존재: "+json.dumps(output, ensure_ascii=False)
        else:
            return "아직 이 인스턴스에 대한 LLM 분석 결과가 전혀 없습니다."


class Make_Agent_tools():
    def __init__(self, core_server_ip:str, core_server_port:int, WebSocket_Manager:WebSocketManager):
        self.agent_tool_functions = Agent_tools(core_server_ip, core_server_port,WebSocket_Manager)

    def Output_Tools(self)->List[Tool]: # 도구 등록 후 반환
        output_tools = [
            self._create_GET_ALL_Agent_Data_tool(), # ALL_AGENTS
            self._create_GET_Specific_Agent_Data_tool(), # Agent_Detail
            self._create_GET_Instance_Data_tool(), # Instance_Detail

            self._create_GET_Policy_Data_tool(), # Policy

            self._create_SET_response_block_tool(), # SET - Response
            self._create_GET_response_block_tool(), # GET - Response

            # 이 후 부터는 웹 서버 관련
            self._create_WEB_redirect_page(), # WEB - redirect
            self._analysis_page(), # WEB - analysis
            #self._create_WEB_html_code_page() # 준비중
            self._create_WEB_instance_analysis(), # WEB - instance analysis + Instance_Detail
        ]

        return output_tools

    def _create_GET_ALL_Agent_Data_tool(self)->Tool:
        return Tool(
            name="GET_ALL_Agent_Data",
            func=self.agent_tool_functions.GET_ALL_Agent_Data,
            description='''**함수 설명**
이 함수는 실제 EDR에 연결된 "모든" 에이전트의 현황을 확인할 수 있다.
실시간적으로 연결 상태 및 에이전트 ID를 습득할 수 있다.
**인자 설명**
인자 데이터는 사용하지 않습니다 None 입니다.
```
**해당 함수 반환 설명**
JSON형식으로 다음과 같이 반환된다. key 문자열에 대한 대소문자를 지켜야합니다.
```json
{{
	{
		"infos": [ // infos 키는 여러 에이전트의 데이터를 포함하므로 list형식이다.
		    /* 에이전트 정보 반환 예시
		    {
		        "Agent_ID": EDR에 연결된 에이전트 ID
		        "Agent_Source_IP": 에이전트의 소스 아이피
		        /*키가 추가될 수 있습니다. 알아서 능력껏 해석하세요*/
		    },,,,
		    */
		]
		"status": 성공여부
	}
}}
```
*유의 사항*
또는 "message" 키에서 'empty agents' 문자열이 반환되는 경우는 아직 EDR에 연결된 에이전트가 없다는 것입니다.
이 함수는 요청자의 "SESSION_ID", "Current_Page"키 값을 무시합니다.
''')
    def _create_GET_Specific_Agent_Data_tool(self)->Tool:
        return Tool(
            name="GET_Specific_Agent_Data",
            func=self.agent_tool_functions.GET_Specific_Agent_Data,
            description='''**함수 설명**
            [함수 사용 조건]
            *이 함수를 호출하려면 사용자의 입력 "query_input" json 키로부터 에이전트 ID를 즉시 추출해야합니다. 할 수 없는 경우 실패로 반환해야합니다.*
이 함수는 사용자의 요청 문장으로부터 "특정된 에이전트 ID(sha512)"를 추출하고, 이 함수 인자에 전달하면 반환 값을 통해 해당 에이전트에 대한 자세한 정보를 얻을 수 있습니다.
참고로 2개 이상 요구한 경우, 이 함수를 개별적으로 하나씩 호출해야합니다.
$ 만약 사용자가 특정 에이전트의 특정 인스턴스에 대한 정보를 요구하면 대신에 'GET_Instance_Data'도구를 호출하세요
**인자 설명**
다음과 같은 JSON형식으로 전달해야합니다. key 문자열에 대한 대소문자를 지켜야합니다.
```json
{
    "agent_id": "EDR에 연결된 에이전트 ID"
}
```
**해당 함수 반환 설명**
다음과 같은 JSON형식으로 반환됩니다. key 문자열에 대한 대소문자를 지켜야합니다.
```json
{
    "status": "success" 또는 "fail",// 응답 성공 여부 및 에이전트 존재 여부
    "info": {
        "Agent_ID": "EDR에 연결된 에이전트 ID",
        "instances": [ // 해당 에이전트에 생성된 프로세스 인스턴스들 목록 
            /* 인스턴스 반환 예시 
            {
                "Instance_ID": "프로세스 인스턴스 ID",
                "Instance_info": { // 프로세스 행위에 관한 정보가 json형식으로 있음.
                    "behavior": {
                        "image": { // 예를 들어 해당 프로세스에서 "이미지 로드"에 관한 behavior인 경우,,,
                            "events_len": int, // 이미지 로드 행위의 이벤트 개수
                            "this_behavior_llm_latest_eval": "", // 해당 이벤트에 대한 분석 평가(여러 개 중 최신 결과 값) 
                        },,, 
                    }
                }, 
                "is_alive": true 또는 false, // 인스턴스 활성 여부, 프로세스가 현재 살아있는 지 확인가능.
                "child_instances": [] // 자식 인스턴스 목록, 이 요소들은 '인스턴스 반환 여부'와 같은 형식이다.
            }    
            */
        ]
    }
    
}
```
*유의 사항*
예상과 다른 값이 반환되는 경우 실패처리하십시오.
이 함수는 요청자의 "SESSION_ID", "Current_Page"키 값을 무시합니다.
'''
        )
    def _create_GET_Instance_Data_tool(self)->Tool:
        return Tool(
            name="GET_Instance_Data",
            func=self.agent_tool_functions.GET_Instance_Data,
            description='''**함수 설명**
            [함수 사용 조건]
            *이 함수를 호출하려면 사용자의 입력 "query_input" json 키로부터 에이전트 ID와 인스턴스 ID 2개를 즉시 추출해야합니다. 할 수 없는 경우 실패로 반환해야합니다.*
            이 함수를 실행하기 전에, 무조건 EDR내에서 포함된 에이전트 ID(sha512)이 있을 때 사용할 수 있습니다.
            이 함수는 특정 에이전트가 가지고 있는 엔드포인트에서 수집된 특정 1개의 인스턴스의 정보를 추출하는 데에 사용됩니다.
            여러 인스턴스를 요구한 경우 이를 여러 번 개별적으로 호출해야합니다. 
        **인자 설명**
        다음과 같은 JSON형식으로 전달해야합니다. key 문자열에 대한 대소문자를 지켜야합니다.
        ```json
        {
            "agent_id": "EDR에 연결된 에이전트 ID" 
            "instance_id": "특정 인스턴스 ID"
        }
        ```
        **해당 함수 반환 설명**
        다음과 같은 JSON형식으로 반환됩니다.
        ```json
        {
            "status": "success" 또는 "fail",// 응답 성공 여부 및 에이전트 존재 여부
            "info": {
                "Agent_ID": "EDR에 연결된 에이전트 ID",
                "instance": { // 찾은 인스턴스의 정보 1개를 반환하는 key
                    /* 인스턴스 반환 예시 
                    {
                        "Instance_ID": "프로세스 인스턴스 ID",
                        "Instance_info": { // 프로세스 행위에 관한 정보가 json형식으로 있음.
                            "behavior": {
                                "image": { // 예를 들어 해당 프로세스에서 "이미지 로드"에 관한 behavior인 경우,,,
                                    "events_len": int, // 이미지 로드 행위의 이벤트 개수
                                    "this_behavior_llm_latest_eval": "", // 해당 이벤트에 대한 분석 평가(여러 개 중 최신 결과 값) 
                                },,, 
                            }
                        }, 
                        "is_alive": true 또는 false, // 인스턴스 활성 여부, 프로세스가 현재 살아있는 지 확인가능.
                        "child_instances": [] // 자식 인스턴스 목록, 이 요소들은 '인스턴스 반환 여부'와 같은 형식이다.
                    }    
                    */
                }
            }
        }
        ```
        *유의 사항*
예상과 다른 값이 반환되는 경우 실패처리하십시오.
이 함수는 요청자의 "SESSION_ID", "Current_Page"키 값을 무시합니다.
        '''
        )
    def _create_GET_Policy_Data_tool(self)->Tool:
        return Tool(
            name="GET_Policy_Data",
            func=self.agent_tool_functions.GET_Policy_Data,
            description='''-> Action: GET_Policy_Data

**함수 설명:**

이 함수는 EDR 시스템에 현재 설정된 정책을 가져오는 도구입니다.

**인자 설명:**

현재 EDR에 적용된 모든 정책을 가져오기 때문에 인자는 필요가 없습니다.

**해당 함수 반환 설명:**

이 도구를 사용하면 EDR 시스템에 적용된 정책을 **JSON 형식**으로 반환합니다. **이 도구를 호출한 후에는 반환된 JSON 데이터를 분석하여 사용자에게 필요한 정보를 제공해야 합니다. 데이터를 성공적으로 얻은 후에는 이 도구를 다시 호출할 필요가 없습니다.**

**예시:**

```json
{'message': // 이는 EDR 서버에서 기본적으로 반환하는 키입니다.
{
    "Analysis_Policy": {  // 분석 실시 정책
        "Analysis_Server_IP": "127.0.0.1",  // 분석 서버 IP
        "Analysis_Server_Port": 5070,  // 분석 서버 포트
        "Detail_Policy": {}  // 상세 정책 -> 현재는 설정되지 않았습니다. 향후 상세 정책이 추가될 수 있습니다.
    },
    "LLM_Policy": {  // LLM 활용 분석 실시 정책
        "EVENT_MIDDLE_EVAL": {  // 중간 평가 실시 정책 (각 유형 평가 결과 총 개수를 기반으로 LLM 기반 악성 분석을 요구)
            "Start_LLM_EVAL_all_count": 1  // "유형 평가"에서의 이벤트 총 개수가 지정되며, 해당 숫자 이상이면 중간 평가 실시. (이 수가 작으면 LLM 요청 부하가 발생할 수 있음)
        },
        "EVENT_TYPE_EVAL": {  // 유형 평가 실시 정책 (각 유형(파일 시스템, 레지스트리, 네트워크, 이미지 로드 등)별로 LLM 기반 행위 요약을 트리거)
            "Start_LLM_EVAL_count": 10  // "유형 평가"는 특정 OS/프로세스 행위(레지스트리, 이미지 로드, 네트워크 등)의 이벤트 수 커트라인. 이 수를 넘으면 "유형 평가" 실시. (이 수가 작으면 LLM 요청 부하가 발생할 수 있음)
        }
    },
    "status": "success"  // 정책 얻어오기: "success" - 성공, "fail" - 실패
}
}
```

**결과 해석 팁:**

이 JSON 값을 사용자에게 **말로 풀어서 설명**하면 더 좋은 신뢰도를 얻을 수 있습니다. 예를 들어, "현재 분석 서버 IP는 127.0.0.1이고, 포트는 5070으로 설정되어 있습니다."와 같이 설명할 수 있습니다.

**경고:**

*   이 도구는 **한 번만 호출**해야 합니다. **반복 호출은 시스템 오류, 무한 루프 및 예기치 않은 동작을 유발할 수 있습니다.**
*   `GET_Policy_Data` 도구는 "SESSION_ID"와 "Current_Page" 관계없이 **한 번만 호출**되어야 합니다.''')

    def _create_SET_response_block_tool(self)->Tool:
        return Tool(
            name="SET_response_block",
            func=self.agent_tool_functions.SET_response_block,
            description='''
            **함수 설명**
        이 함수는 EDR에 연결된(온라인 및 오프라인 해당)에이전트에게 차단을 등록하는 함수입니다.
        차단은 총 3가지로 1. 프로세스 차단, 2. 네트워크 차단, 3. 파일 차단 으로 구분됩니다.
        파일 및 프로세스 차단은 SHA256값과 파일 사이즈 2개를 사용자 요청을 추출해서 인수를 생성하고,
        네트워크 차단은 string타입의 IP주소를 하나를 사용자 요청 문장을 추출해서 인수를 생성해야합니다.
        또한 차단 타겟을 정확히 지정하기 위해서는 에이전트 ID(sha512)를 사용자 요청 문장으로부터 추출해야합니다.
        **인자 설명**
        다음과 같은 JSON형식으로 전달해야합니다. key 문자열에 대한 대소문자를 지켜야합니다.
        ```json
        {
            "responses": [] // 사용자가 차단 요청을 여럿한 경우를 대비하기 위해 list로 전달합니다.
            /*
                예시 값은 다음과 같습니다.
                [
                    {
                        "response_type": "process", // 프로세스 차단. 만약 파일 차단을 요구한 경우, "file"로 대체한다.
                        "SHA256": "SHA256...", // 이미 존재하는 SHA256값을 사용자 요청
                        "file_size": 1024, // 파일 사이즈를 사용자 요청
                        "agent_id": ""// 차단 타겟을 위한 에이전트 ID
                    },
                    {
                        "response_type": "network", // 네트워크 차단
                        "remoteip": "8.8.8.8", // IP주소를 추출해서 다음과 같이 진행. IPv4형태여야만 한다.
                        "agent_id": ""// 차단 타겟을 위한 에이전트 ID
                    }
                ]
            */
        }
        ```
        **해당 함수 반환 설명**
        성공 여부를 확인할 수 있으며, 성공 및 실패와 관련하여 반환된 경우 이를 사용자에게 유연하게 응답하세요.
        
        *유의 사항*
        이 함수에서 차단 3가지 방식을 완벽히 호출하기 위해서는 사용자가 요청한 것을 정확히 추출해야하며, 만약 추출이 불가능한 경우는, 상기 설명된 것을 기반으로 사용자에게 올바르게 요청하도록 방법을 다시 알려야합니다.(JSON형식이 아닌 자연어로만)
        오로지 사용자 문장으로부터 추출이 가능해야만 이 함수는 성공합니다.
이 함수는 요청자의 "SESSION_ID", "Current_Page"키 값을 무시합니다.
        '''
        )

    def _create_GET_response_block_tool(self) -> Tool:
        return Tool(
            name="GET_response_block_list",
            func=self.agent_tool_functions.GET_response,
            description='''
            *함수 설명*
            이 함수는 특정 에이전트에 현재 등록된 차단 정보를 list 형태로 가져옵니다.
            *인수 설명*
            당신은 사용자의 요청문으로부터 에이전트 ID를 스스로 추출해야합니다. 만약 그것이 불가능하다고 생각하면 사용자에게 올바른 에이전트 ID를 요구하십시오. 
            당신은 다음과 같은 JSON형식의 인수를 생성해야합니다.
            ```json
            {
                "agent_id": "EDR에 연결된 에이전트 ID"
            }
            ```
            *해당 함수 반환 설명*
            JSON형식으로 다음과 같이 반환될 수 있습니다.
            ```json
            {
                "message": {
                    "infos": [
                        {
                            "response_type": "process", // 프로세스 인스턴스 차단 정보
                            "sha256": "SHA256...", // 이미 존재하는 SHA256값을 사용자 요청
                            "file_size": 1024, // 파일 사이즈를 사용자 요청
                            "remoteip": "8.8.8.8", // 이미 존재하는 IP주소를 사용자 요청
                        },,,,
                    ]
                }
            }
            *유의 사항*
            반환되는 값은 [] 리스트 형태로 제공됩니다.
            [] 인 경우는 아직 차단 정보가 하나도 없는 것이며,
            [] 안에는 여러 개의 JSON 객체가 존재합니다. 
            response_type은 다음과 같습니다.
            - process: 프로세스 인스턴스 차단
            - network: 네트워크 인스턴스 차단
            - file: 파일 인스턴스 차단
            
            나타날 수 있는 key들은 다음과 같습니다.
            "response_type": "process",  // 프로세스 인스턴스 차단 정보 또는 network, file 중 하나
            "sha256": "SHA256...", // 파일 및 프로세스 파일에 관한 SHA256값
            "file_size": 1024, // 파일 및 프로세스 파일에 관한 SHA256값
            "remoteip": "8.8.8.8", // network 차단에서 원격지 IP주소
            '''
        )

    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    ###############################################################################################################################################
    # [웹 페이지 관련 Tool]

    def _create_WEB_redirect_page(self)->Tool:
        return Tool(
            name="WEB_redirect_the_page",
            func=self.agent_tool_functions.WEB_redirect_page,
            description='''
            -> Action: WEB_redirect_the_page
            
            **함수 설명**
            *사용자가 리다이렉트를 요청한 경우 의무적으로 이 도구를 한번 사용하고 Final Answer 해야합니다.*
            당신은 그저 URL 주소와 필요의 경우 파라미터까지 포함된 URL을 만드는 역할만 수행해야합니다. 함부로 다른 도구를 사용해서는 안됩니다.
            실제 리다이렉트는 내부에서 처리되므로 당신이 관여할 필요가 없습니다.
            
            이 함수는 특정 HTTP 클라이언트 사용자(요청자)가 특정 페이지로 리다이렉트를 원할 때 사용하는 함수이다.(아래 각각의 페이지 설명에서와 같이 함수 인수를 생성하여 사용하세요)
            
            당신은 다음과 같은 페이지에 접근이 가능합니다.
            [리다이렉트 가능한 페이지]
            1. 페이지: "/Agents", 인자개수: 0, 인자 명: [없음], 설명: EDR에 등록된 에이전트 확인 페이지.
            2. 페이지: "/Agent_Detail", 인자개수: 1, 인자 명: ["agent_id"], 설명: EDR에 등록된 에이전트 1개에 대한 상세 페이지. 예시(/Agent_Detail?agent_id=... 형식이며 agent_id에는 사용자로부터 에이전트 아이디를 얻어야합니다)
            3. 페이지: "/Instance_Detail", 인자개수: 2, 인자 명: ["agent_id", "instance_id"], 설명: EDR에 등록된 에이전트 1개에 대한 인스턴스 페이지. 예시(/Instance_Detail?agent_id=...?instance_id=... 형식이며, 에이전트 ID 및 인스턴스 ID는 사용자의 query문에서 파악해서 지정하세요.)
            **인자 설명**
            다음과 같은 JSON형식으로 인수를 만들어야합니다. 
            ```json
            {
                "SESSION_ID": "요청자가 전달한 "SESSON_ID"키의 값을 그대로 여기에 지정합니다.",
                "sub_web_dir": 설명한 '리다이렉트 가능한 페이지'를 기반으로 "페이지"를 지정합니다. ex) "/Agents" 또는 "/Agent_Detail"
                "arguments": {
                    /*
                        "sub_web_dir" 키에 알맞는 인자들을 json에 추가한다. (만약 없는 경우는 {}으로 공란하시오. )
                        
                        ex1) "sub_web_dir" 키의 값이 /Agent_Detail 인 경우, 
                        {
                            "agent_id": "요청자가 전달한 agent_id를 그대로 여기에 지정합니다."
                        }
                        
                        ex2) "sub_web_dir" 키의 값이 /Instance_Detail 인 경우,
                        {
                            "agent_id": "요청자가 전달한 agent_id를 그대로 여기에 지정합니다.",
                            "instance_id": "요청자가 전달한 instance_id를 그대로 여기에 지정합니다."
                        }
                        
                    */
                    
                }
            }
            ```
             **해당 함수 반환 설명**
             성공 또는 실패로 확인되며
             성공시에는 {"cmd": "WEB_redirect_the_page", "data": "리다이렉트로 만들어진 url값"} 형식으로 반환되며, 이 데이터 그대로 JSON형식으로 Final Answer 하십시오.
            실패시에는 자연어 text형식으로 실패했다고 자연스럽게 Final Answer 하십시오.
            '''
        )

    # 페이지 분석 ( 사실은 그것이 아니지만 )
    def _analysis_page(self)->Tool:
        return Tool(
            name="analysis_page",
            func=self.agent_tool_functions.analysis_page,
            description='''
            -> Action: analysis_page
            
            **함수 설명**
            이 함수는 요청자의 JSON에서 "Current_Page"키의 값으로부터 페이지를 분석하는 것입니다. 
            예를 들어 "query_input"키의 값이 "이 페이지를 분석해줘", "이 페이지를 좀 더 해석해주거나 이해시켜줘"등 사용자가 현재 위치한 페이지에서의 내용에 대해 분석이 필요한 경우, 이 도구/함수를 호출해야합니다.
            **인자 설명**
            JSON형식으로 다음과 같이 인수를 생성하여 함수를 호출해야합니다
            ```json
            {
                "sub_dir": "요청하고 있는 하위 디렉터리 명", // ex) "/Agents", "/Agent_Detail"(이는 사용자의 입력으로부터 에이전트 ID 하나만 식별될 때 지정하십시오.), "/Instance_Detail"(이는 사용자의 입력으로부터 에이전트 ID와 인스턴스 ID 2개가 식별될 때 지정하십시오.) 등
                "parameters": { // sub_dir 의 설정된 파라미터가 있는 경우 다음과 같이 지정합니다. 
                    "파라미터명": "파라미터값" // ex) "agent_id": "EDR에 등록된 에이전트 ID"
                    // 파라미터가 2개이면 그 수에 맞게 동적 지정하세요.
                }
            }
            ```
            **해당 함수 반환시 당신이 해야하는 일**
            이 함수는 sub_dir과 설정된 파라미터에 따라 실제 JSON형식의 데이터를 가져와서 유연하게 사용자가 입력한 "query_input"에 맞게 응답 메시지를 당신이 스스로 생성하여 즉시 반환합니다.
            1. sub_dir값이 "/Agents"인 경우 반환되는 JSON 형식 예시는 다음과 같습니다.
            ```json
{{
	{
		"infos": [ // infos 키는 여러 에이전트의 데이터를 포함하므로 list형식이다.
		    /* 에이전트 정보 반환 예시
		    {
		        "Agent_ID": EDR에 연결된 에이전트 ID
		        "Agent_Source_IP": 에이전트의 소스 아이피
		        /*키가 추가될 수 있습니다. 알아서 능력껏 해석하세요*/
		    },,,,
		    */
		]
		"status": 성공여부
	}
}}
```
            2. sub_dir값이 "/Agent_Detail"인 경우 반환되는 JSON 형식 예시는 다음과 같습니다.
            ```json
{
    "status": "success" 또는 "fail",// 응답 성공 여부 및 에이전트 존재 여부
    "info": {
        "Agent_ID": "EDR에 연결된 에이전트 ID",
        "instances": [ // 해당 에이전트에 생성된 프로세스 인스턴스들 목록 
            /* 인스턴스 반환 예시 
            {
                "Instance_ID": "프로세스 인스턴스 ID",
                "Instance_info": { // 프로세스 행위에 관한 정보가 json형식으로 있음.
                    "behavior": {
                        "image": { // 예를 들어 해당 프로세스에서 "이미지 로드"에 관한 behavior인 경우,,,
                            "events_len": int, // 이미지 로드 행위의 이벤트 개수
                            "this_behavior_llm_latest_eval": "", // 해당 이벤트에 대한 분석 평가(여러 개 중 최신 결과 값) 
                        },,, 
                    }
                }, 
                "is_alive": true 또는 false, // 인스턴스 활성 여부, 프로세스가 현재 살아있는 지 확인가능.
                "child_instances": [] // 자식 인스턴스 목록, 이 요소들은 '인스턴스 반환 여부'와 같은 형식이다.
            }    
            */
        ]
    }
    
}
```
            3. sub_dir값이 "/Instance_Detail"인 경우 반환되는 JSON 형식 예시는 다음과 같습니다.
            ```json
{'message': // 이는 EDR 서버에서 기본적으로 반환하는 키입니다.
{
    "Analysis_Policy": {  // 분석 실시 정책
        "Analysis_Server_IP": "127.0.0.1",  // 분석 서버 IP
        "Analysis_Server_Port": 5070,  // 분석 서버 포트
        "Detail_Policy": {}  // 상세 정책 -> 현재는 설정되지 않았습니다. 향후 상세 정책이 추가될 수 있습니다.
    },
    "LLM_Policy": {  // LLM 활용 분석 실시 정책
        "EVENT_MIDDLE_EVAL": {  // 중간 평가 실시 정책 (각 유형 평가 결과 총 개수를 기반으로 LLM 기반 악성 분석을 요구)
            "Start_LLM_EVAL_all_count": 1  // "유형 평가"에서의 이벤트 총 개수가 지정되며, 해당 숫자 이상이면 중간 평가 실시. (이 수가 작으면 LLM 요청 부하가 발생할 수 있음)
        },
        "EVENT_TYPE_EVAL": {  // 유형 평가 실시 정책 (각 유형(파일 시스템, 레지스트리, 네트워크, 이미지 로드 등)별로 LLM 기반 행위 요약을 트리거)
            "Start_LLM_EVAL_count": 10  // "유형 평가"는 특정 OS/프로세스 행위(레지스트리, 이미지 로드, 네트워크 등)의 이벤트 수 커트라인. 이 수를 넘으면 "유형 평가" 실시. (이 수가 작으면 LLM 요청 부하가 발생할 수 있음)
        }
    },
    "status": "success"  // 정책 얻어오기: "success" - 성공, "fail" - 실패
}
}
```
JSON형식을 해석한 경우 이제 Final Answer 하십시오.
            '''
        )

    # 웹 페이지 자가 생성 함수
    def _create_WEB_html_code_page(self)->Tool:
        return Tool(
            name="WEB_create_html_for_a_user",
            func= self.agent_tool_functions.WEB_create_html_code_page,
            description='''
            -> Action: WEB_create_html_for_a_user
            
            *당신이 스스로 사용자에게 가시화 높은 정보로 HTML코드를 통해 제공하려면 이 도구를 한번 사용하고 Final Answer 해야합니다.*
            당신은 다음과 같은 Sample HTML의 스타일(body제외, css, UI분위기등 )들을 참조하여 사용자가 요구하는 HTML을 직접 만들어서 반환해야합니다.
            참고사항: HTML에 넣을 content를 얻으려면 당신이 사용할 수 있는 도구를 사전에 호출해야 할 수 있습니다. 그리고 "<div class="flex flex-1 justify-end gap-8"> 영역" 는 그 어떤 생성된 페이지든 간에 시그니처 헤더 네비게이션이므로, 의무적으로 추가해야합니다.
            
            
            [Sample HTML]
             <!DOCTYPE html>
<html>
<head>
    <link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin="" />
    <link
        rel="stylesheet"
        as="style"
        onload="this.rel='stylesheet'"
        href="https://fonts.googleapis.com/css2?display=swap&family=Noto+Sans%3Awght%40400%3B500%3B700%3B900&family=Plus+Jakarta+Sans%3Awght%40400%3B500%3B700%3B800"
    />
    <title>Galileo Design</title>
    <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64," />
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
</head>
<body class="bg-[#131C24] text-[#F8F9FB]" style='font-family: "Plus Jakarta Sans", "Noto Sans", sans-serif;'>
    <!-- Header -->
    <header class="flex items-center justify-between whitespace-nowrap border-b border-solid border-b-[#29374C] px-10 py-3">
        <div class="flex items-center gap-4 text-[#F8F9FB]">
            <div class="size-4">
                <svg viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M4 42.4379C4 42.4379 14.0962 36.0744 24 41.1692C35.0664 46.8624 44 42.2078 44 42.2078L44 7.01134C44 7.01134 35.068 11.6577 24.0031 5.96913C14.0971 0.876274 4 7.27094 4 7.27094L4 42.4379Z" fill="currentColor" />
                </svg>
            </div>
            <h2 class="text-[#F8F9FB] text-lg font-bold leading-tight tracking-[-0.015em]">Lumina Sentinel</h2>
        </div>
        <div class="flex flex-1 justify-end gap-8">
            <div class="flex items-center gap-9">
                <a class="text-[#F8F9FB] text-sm font-medium leading-normal" href="#">Dashboard</a>
                <a class="text-[#F8F9FB] text-sm font-medium leading-normal" href="#">Agent</a>
                <a class="text-[#F8F9FB] text-sm font-medium leading-normal" href="#">Module</a>
                <a class="text-[#F8F9FB] text-sm font-medium leading-normal" href="#">LLM</a>
                <a class="text-[#F8F9FB] text-sm font-medium leading-normal" href="#">Setting</a>
            </div>
            <button class="flex min-w-[84px] max-w-[480px] cursor-pointer items-center justify-center overflow-hidden rounded-xl h-10 px-4 bg-[#F4C753] text-[#141C24] text-sm font-bold leading-normal tracking-[0.015em]">
                <span class="truncate">Help</span>
            </button>
            <div class="bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10" style='background-image: url("https://cdn.usegalileo.ai/sdxl10/5245e422-a076-4fa8-b754-8e9cc9557d73.png");'></div>
        </div>
    </header>

    <div class="container mx-auto px-4 py-8">
        <!-- Main Content Example with Tabs -->
        <main class="mt-8">
            <h2 class="text-2xl font-bold mb-4">Section Title</h2>
            <!-- Tabs -->
            <div class="flex border-b border-[#32415D] mb-4">
                <button class="tab-button px-4 py-2 font-bold text-sm border-b-2 border-transparent hover:text-[#F4C753] hover:border-[#F4C753]">Tab 1</button>
                <button class="tab-button px-4 py-2 font-bold text-sm border-b-2 border-transparent hover:text-[#F4C753] hover:border-[#F4C753]">Tab 2</button>
            </div>
            <!-- Tab Content -->
            <div class="tab-content">
                <!-- Example Content -->
                <div class="flex items-center gap-4 bg-[#131C24] p-4 border border-[#29374C] rounded-lg">
                    <div class="text-[#F8F9FB] flex items-center justify-center rounded-lg bg-[#29374C] shrink-0 size-12">
                        <!-- Placeholder for Icon -->
                        <svg width="24" height="24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path>
                            <path d="m22 6-10 7L2 6"></path>
                        </svg>
                    </div>
                    <div>
                        <p class="font-medium">Item Name</p>
                        <p class="text-sm text-[#8A9DC0]">Item Description</p>
                    </div>
                </div>
            </div>
        </main>
    </div>
</body>
</html>
[함수 호출 인자]
인자는 JSON형식이며 당신이 요청자에 맞게 Sample HTML 기반으로 생성한 HTML코드롸 SESSION_ID 키 총 2개를 인수를 만들어야합니다.
```json
{
    "SESSION_ID": "요청자가 전달한 SESSION_ID를 그대로 여기에 지정합니다.",
    "HTML_CODE": "" // 문자열의 실제로 작동가능한 HTML코드.
}
```
[함수 호출 후 반환 형식]
성공과 실패로 구분되며,
성공시에는 {"cmd": "WEB_create_html_for_a_user", "data": "생성된 HTML_CODE"} 형식으로 반환되며, 이 데이터 그대로 JSON형식으로 Final Answer 하십시오.
실패라고 판단되는 경우 "실패"관련한 text문장으로 반환하십시오.
그리고 바로 Final Answer 하세요.
            '''
        )

    def _create_WEB_instance_analysis(self)->Tool:
        return Tool(
            name="WEB_instance_analysis",
            func=self.agent_tool_functions.WEB_instance_analysis,
            description='''
            -> Action: WEB_instance_analysis
            
            ** 도구 사용 조건 **
            이 함수는 요청자의 JSON에서 "Current_Page"키의 URL값이 "Instance_Detail"이거나, Insatnce_id 키가 꼭 식별되어야 하며 사용자가 특정 에이전트의 인스턴스에 대해 분석을 요구할 때 이 도구를 사용할 수 있습니다.
            
            **함수 설명**
            이 함수/도구는 특정 에이전트에 속한 특정 프로세스 인스턴스의 LLM 분석 결과를 생성한 이력을 반환합니다.
            
            **인자 설명**
            다음과 같은 JSON형식으로 인수를 만들어야합니다. 
            ```json
            {
                "Instance_id": "{SHA256....}"// 요청자가 전달한 Instance_id 키의 값(SHA512)이며 이는 당신 스스로 요청자로부터 식별해서 인스턴스 ID값(오로지 해시값)을 여기에 지정해야합니다.
            }
            ```
            [함수 호출 후 반환 형식]
            이 도구는 다음과 같이 반환되며, 이 반환된 값을 기반으로 해당 Instance에서 수집된 분석 정보를 통해 응답하십시오.
            ```json
            {
                "result": [] // 이는 List[Dict] 형태로 동적으로 결과를 반환합니다. 
                /*
                    예시 값
                    "result" : [
                        {
                            "EDR": "{,,,}", // 분석을 위해 요청한 데이터. 타입이 str 또는 JSON일 수 있으며, 미리 분석된 정보가 포함될 수 있습니다.
                            /*
                                "EDR" 키 값 설명
                                - "TYPE" 키 값이 "MIDDLE_EVAL"인 경우, 이는 중간 평가를 EDR이 요청한 것이다.
                                - "FINAL_EVAL" 인 경우, 이는 중간 평가를 EDR이 요청한 것이다.
                            */
                            "LLM": "{,,,}" // 요청한 데이터에 대한 LLM 분석 결과. 타입이 str 또는 JSON일 수 있습니다. 미리 분석된 정보가 포함될 수 있습니다.
                            "LLM" JSON 예시
                             -- *   `summary`: 프로세스의 모든 행위를 종합적으로 요약한 문장입니다.
*   `anomaly_score`: 객관적이고 심층적인 분석을 통해 악성코드 가능성 점수를 0점에서 100점 사이로 제공됨.
    *   **0점:** 악성 행위 없음
    *   **100점:** 매우 확실한 악성 행위
    *   **주의:** False Positive를 최소화하기 위해 신중하게 점수를 부여한 값. 모든 상황을 차단하기보다는, 악성 가능성이 높은 경우에만 높은 점수를 부여하도록 주의됨.
*   `report`: 분석 근거를 상세히 설명하는 보고서
    *   **대상:** EDR 고객의 최종 보안 관리자
    *   **내용:**
        *   전체 행위 요약
        *   주요 특징 추출 및 상세 서술 (학술 논문 수준의 상세함 요구)
        *   악성 의심 근거 명시 (False Positive 최소화를 위한 구체적 근거 제시)
        *   권장 대응 방안 (필요 시)
*   `tags` : List[str]형식으로 해당 이벤트에 대한 태그, 카테고리 등, 당신 스스로 분석 신뢰성을 높이기 위하여 이 이벤트들에 대한 요약을 단어들로 카테고리 
                        }
                    ]
                */
            }
            ```
            '''
        )