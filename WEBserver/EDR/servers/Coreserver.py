import requests, json


class CoreServerAPI():
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        
        self.HTTP_connection = f"http://{self.host}:{self.port}"
    
    # 실시간 에이전트 연결 현황
    def Get_Live_Agents(self)->list[dict]:
        url = f"{self.HTTP_connection}/request/view/agents"
        response = requests.get(url).json()
        try:
            response = json.loads(response["output"])
        except:
            response =  []
        finally:
            return response
        
    def CoreServer_agent_response_process(self, agent_id:str, sha256:str, filesize:int, is_remove:bool=False)->dict:
        url = f"{self.HTTP_connection}/request/response/process"
        params = {
            "agent_id": agent_id,
            "sha256": sha256,
            "filesize": filesize,
            "is_remove": is_remove
        }
        response = requests.get(
            url=url,
            params=params
        ).json()
        
        return response  

    # 파일
    def CoreServer_agent_response_file(self, agent_id:str, sha256:str, filesize:int, is_remove:bool=False)->dict:
        url = f"{self.HTTP_connection}/request/response/file"
        params = {
            "agent_id": agent_id,
            "sha256": sha256,
            "filesize": filesize,
            "is_remove": is_remove
        }
        response = requests.get(
            url=url,
            params=params
        ).json()
        
        return response  

    # 네트워크
    def CoreServer_agent_response_network(self, agent_id:str,  remoteip:str, is_remove:bool=False)->dict:
        url = f"{self.HTTP_connection}/request/response/network"
        params = {
            "agent_id": agent_id,
            "remote_ip": remoteip,
            "is_remove": f"{is_remove}"
        }
        response = requests.get(
            url=url,
            params=params
        ).json()
        
        return_bool = False
        try:
            if isinstance(response["message"], bool):
                return_bool = response["message"]
            elif isinstance(response["message"], str):
                return_bool = bool(response["message"])
            else:
                return_bool = False
        except:
            return_bool = False
            
        return return_bool  

    # 에이전트 차단 리스트 조회    
        
    
        