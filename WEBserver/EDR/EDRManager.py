from typing import Optional, Tuple

class EDR_Manager():
    def __init__(
        self,
        
        CoreServer_host: str, 
        CoreServer_port: int,
        
        ElasticSearch_host: str, 
        ElasticSearch_port: int,
        
        Kibana_host: str, 
        Kibana_port: int,
        
    ):
        from EDR.servers.Coreserver import CoreServerAPI
        self.CoreServerAPI = CoreServerAPI(host=CoreServer_host, port=CoreServer_port)
        
        
        from EDR.servers.Elasticsearch import ElasticsearchAPI
        self.ElasticsearchAPI = ElasticsearchAPI(host=ElasticSearch_host, port=ElasticSearch_port)
        
        from EDR.servers.Kibana import KibanaAPI
        self.KibanaAPI = KibanaAPI(host=Kibana_host, port=Kibana_port, es=self.ElasticsearchAPI)
        
    
    # 모든 에이전트 정보 추출
    def Get_Agents(self)->Optional[list[dict]]:
        '''
            TODO: 에이전트 조회
            LOGIC: 
                1) ElasticsearchAPI 쿼리 -------------> 에이전트 전체
                2) 코어서버 실시간 에이전트 조회하여 ---> 에이전트 활성화 여부 체크
        '''
        
        # 연결된 이력이 있는 것 가져오기
        query = {
            "size": 0,  # 문서 자체는 반환하지 않고 집계 결과만 받기 위함
            "aggs": {
                "agent_id_filter": {  # 집계 결과에 대한 임의의 이름
                    "terms": {
                        "field": "categorical.Agent_Id",
                        # 고유값을 추출할 필드 (.keyword 사용 권장)
                        "size": 10000  # 반환받을 고유값의 최대 개수 (필요에 따라 조절)
                    },
                    "aggs": {
                        "agent_id_top_filter": {  # 3. 필터링된 결과 중 상위 문서(여기선 1개) 가져오기
                            "top_hits": {
                                "size": 1,  # ImagePath가 있는 문서 중 1개만 가져옴
                                "_source": [  # 가져올 필드 지정
                                    "categorical.Agent_Id",
                                    "categorical.Agent_status", # boolean 타입이며, 활성여부를 "최신으로 가져와야함"
                                    "categorical.OS_info"
                                ],
                                # 필요하다면 정렬 기준 추가 (예: 가장 오래된/최신 )
                                "sort": [ { "@timestamp": "asc" } ]
                            }
                        }
                    }

                }
            }
        }
        result = self.ElasticsearchAPI.Query(query=query, index="siem-edr-*", is_aggs=True)
        
        # 에이전트 실시간 조회
        live_agents = self.CoreServerAPI.Get_Live_Agents()
        live_agent_ids = [agent["Agent_ID"] for agent in live_agents['agents']]
        
        output:Optional[list[dict]] = []
        # parse
        agents:list[dict] = result["agent_id_filter"]["buckets"]
        if len(agents) > 0:
            for agent_info in agents:
                agent_id = agent_info["key"]
                
                # coreserver 조회한 결과와 비교하여 실시간 여부 체크
                health_check = False
                if agent_id in live_agent_ids:
                    health_check = True
                
                # _source 추출
                os = agent_info["agent_id_top_filter"]["hits"]["hits"][0]["_source"]["categorical"]["OS_info"]

                output.append(
                    {
                        "agent_id": agent_id,
                        "status": health_check,
                        "os": os
                    }
                )
        else:
            return None
        
        return output
    
    # 특정 에이전트, 모든 ROOT 프로세스 사이클 추출
    def Get_Processes(self, agent_id:str, root_process_limit_size:int=50)->Optional[list[dict]]:
        '''
            TODO: 특정 에이전트의 "프로세스 정보 조회"
            LOGIC: 
                1) ElasticsearchAPI 쿼리 -------------> 프로세스 [ROOT] 사이클 번호 조회
                2) CoreServerAPI 쿼리 -------------> 프로세스 상태 조회
        '''
        query = {
            "size": 0,  # 문서 자체는 반환하지 않고 집계 결과만 받기 위함
            "query":{
                "bool":{
                    "filter":[
                        {
                            "term":{
                                "categorical.Agent_Id": agent_id
                            }
                        }
                    ]
                }
            },
            "aggs": {
                "unique_root_ids": {
                    "terms": {
                        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",  # 고유값을 추출할 필드 (.keyword 사용 권장)
                        "size": root_process_limit_size  # 반환받을 고유값의 최대 개수 (필요에 따라 조절)
                    },
                    "aggs":{
                        "Process_Created_filter": {
                            "filter": {
                                "exists": { # "exists" 쿼리를 사용하여 해당 필드가 있는지 확인
                                "field": "unique.process_behavior_events.Process_Created"
                                }
                            },
                            "aggs": {
                                "Process_Created_top_filter": {
                                    "top_hits": {
                                        "size":1,
                                        "_source": [  # 가져올 필드 지정
                                            "unique.process_behavior_events.Process_Created",
                                            "categorical"
                                        ],
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        result = self.ElasticsearchAPI.Query(query=query, index="siem-edr-*", is_aggs=True)
        RootProcesses = result["unique_root_ids"]["buckets"]
        output:Optional[list[dict]] = []
        if len(RootProcesses) > 0:
            for RootProcess in RootProcesses:
                output.append(
                    {
                        "root_process_id": RootProcess["key"],
                        "Process_Created": RootProcess["Process_Created_filter"]["Process_Created_top_filter"]["hits"]["hits"][0]["_source"]["unique"]["process_behavior_events"]["Process_Created"],
                        "categorical": RootProcess["Process_Created_filter"]["Process_Created_top_filter"]["hits"]["hits"][0]["_source"]["categorical"]
                    }
                )
        else:
            return None
        
        return output
        
    # Root 프로세스 사이클 -> 트리구조 반환
    def Get_Process_Tree(self, root_process_id:str, index="siem-edr-*")->Tuple[ Optional[dict], Optional[str] ]:
        from EDR.process_.process_tree import Process_Tree_Maker
        
        # [1/2] 실제 Root 프로세스 사이클 기반, Tree구조 생성
        output_tree_dict, output_mermaid_graph = Process_Tree_Maker(
                                                        es=self.ElasticsearchAPI,
                                                        INDEX_PATTERN=index
                                                    ).Create_Process_Tree(
                                                        Root_Process_Life_Cycle_Id=root_process_id
                                                    )

        
        return output_tree_dict, output_mermaid_graph