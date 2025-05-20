from copy import deepcopy
from typing import Optional, Dict

from elasticsearch import Elasticsearch

from EDR.servers.kibana__Utility.queries import *

# 타임스탬프 매니저
from Utility.timestamper import Set_Range_Time

from EDR.servers.Elasticsearch import ElasticsearchAPI

class kibanaDashboard:
    def __init__(self, es:ElasticsearchAPI, INDEX_NAME: str= "siem-edr-",INDEX_PATTERN:str="siem-edr*"):
        self.es = es
        self.INDEX_NAME = INDEX_NAME
        self.INDEX_PATTERN = INDEX_PATTERN

    def ALL_DASHBOARD(self, agent_id:Optional[str]=None, Root_Parent_Process_Life_Cycle_Id:Optional[str]=None, Process_Life_Cycle_id:Optional[str]=None, query_string:str=None,Hours:int=12)->Optional[Dict]:

        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)

        return {
            "타임스탬프_범위": {
              "기준시간": current_time,
              "과거시간": decreased_time,
              "미래시간": increased_time,
            },
            "총_이벤트량": {
                "Kibana_Graph": "Pie",
                "Description": "EDR내 모든 에이전트가 수집한 총 이벤트 카운트수를 행위별로 나타낸 수치",
                "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time, # 시간 범위 설정

                            ALL_EVENTS_Pie_Chart, # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
            },
            "타임스탬프기반_총_이벤트량": {
                "Kibana_Graph": "Area",
                "Description": "EDR내 모든 에이전트가 수집한 총 이벤트; 카운트 수에 대한  행위별 이벤트를 [Timestamp] 별로나타낸 수치",
                "Log": self.query_to_elasticsearch_(
                    self.add_agent_id_or_root_id_into_filter(

                        increased_time, decreased_time,  # 시간 범위 설정

                        ALL_EVENTS_Area_Chart, # 해당 차트에 대한 쿼리

                        agent_id,
                        Root_Parent_Process_Life_Cycle_Id,
                        Process_Life_Cycle_id,
                        query_string
                    )
                )
            }
        }

    def REGISTRY_DASHBOARD(self, agent_id:Optional[str]=None, Root_Parent_Process_Life_Cycle_Id:Optional[str]=None, Process_Life_Cycle_id:Optional[str]=None, query_string:str=None,Hours:int=12)->Optional[Dict]:
        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)
        return {
            "타임스탬프_범위": {
                "기준시간": current_time,
                "과거시간": decreased_time,
                "미래시간": increased_time,
            },
            "이벤트": [

                {
                    "Kibana_Graph": "Area",
                    "Description": "타임라인 별 발생한 [레지스트리] 이벤트 발생 수 확인",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            REGISTRY_BEHAVIOR_timeline_count_EVENTS, # 해당 차트에 대한 쿼리

                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
                },
                {
                    "Kibana_Graph": "Table",
                    "Description": "타임라인 별 '최근' 발생한 [레지스트리] 이벤트 발생 확인",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            REGISTRY_BEHAVIOR_timeline_recently_EVENTS,  # 해당 차트에 대한 쿼리

                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> 레지스트리 키 (함수)
                        "3": "key" -> 레지스트리 Hive 경로 (target path)
                        "4": "key" -> ISO 포맷의 타임스탬프
                    '''
                },
                {
                    "Kibana_Graph": "Pie",
                    "Description": "제일 많이 사용된 레지시트리 키 함수",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            REGISTRY_BEHAVIOR_registry_key_frequency_EVENTS,  # 해당 차트에 대한 쿼리

                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
                }

            ]
        }

    def NETWORK_DASHBOARD(self, agent_id: Optional[str] = None, Root_Parent_Process_Life_Cycle_Id: Optional[str] = None,
                          Process_Life_Cycle_id: Optional[str] = None, query_string:str=None,Hours: int = 12) -> Optional[Dict]:
        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)
        return {
            "타임스탬프_범위": {
                "기준시간": current_time,
                "과거시간": decreased_time,
                "미래시간": increased_time,
            },
            "이벤트": [
                {
                    "Kibana_Graph": "Table",
                    "Description": "최근 네트워크 통신 이력",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            NETWORK_BEHAVIOR_remoteip_recently_remoteip_EVENTS, # 해당 차트에 대한 쿼리

                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> 원격지IP ( remoteip )
                        "3": "key" -> 원격지PORT ( remoteport )
                        "4": "key" -> 프로토콜 ( Protocol )
                        "5": "key" -> 원격지 지역(국가) 정보 ( geoip )
                        "6": "key" -> 해당 원격지 IP에 대한 도메인 정보 ( Org )
                        "7": "key" -> ISO 포맷의 타임스탬프
                    '''
                },
                {
                    "Kibana_Graph": "Bar",
                    "Description": "타임스탬별 발생한 네트워크 이벤트 수",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            REGISTRY_BEHAVIOR_timeline_count_EVENTS,  # 해당 차트에 대한 쿼리

                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Bar_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "1-bucket":  -> UDP, 
                        "2-bucket": -> TCP,
                        "3-bucket": -> ICMP,
                        "4-bucket": -> OTHER ( UDP,TCP, ICMP 제외 프로토콜 )
                    '''
                }
            ]
        }

    def IMAGELOAD_DASHBOARD(self, agent_id: Optional[str] = None,
                            Root_Parent_Process_Life_Cycle_Id: Optional[str] = None,
                            Process_Life_Cycle_id: Optional[str] = None,query_string:str=None, Hours: int = 12) -> Optional[Dict]:
        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)
        return {
            "타임스탬프_범위": {
                "기준시간": current_time,
                "과거시간": decreased_time,
                "미래시간": increased_time,
            },
            "이벤트": [
                {
                    "Kibana_Graph": "Area",
                    "Description": "타임라인 별 발생한 [이미지 로드]이벤트 발생 '종합' 수치 확인",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                        IMAGELOAD_BEHAVIOR_TimeLine_EVENTS,  # 해당 차트에 대한 쿼리

                        agent_id,
                        Root_Parent_Process_Life_Cycle_Id,
                        Process_Life_Cycle_id,
                            query_string
                        )
                    )
                },
                {
                    "Kibana_Graph": "Table",
                    "Description": "타임라인 별 발생한 [이미지 로드]이벤트 발생 상세 건 확인",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                        IMAGELOAD_BEHAVIOR_recently_EVENTS,  # 해당 차트에 대한 쿼리

                        agent_id,
                        Root_Parent_Process_Life_Cycle_Id,
                        Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> 이미지 파일 SHA256 값
                        "3": "key" -> 이미지(dll, exe) 풀 네임
                        "4": "key" -> ISO 포맷의 타임스탬프
                    '''
                }
            ]
        }

    def FILESYSTEM_DASHBOARD(self, agent_id: Optional[str] = None,
                             Root_Parent_Process_Life_Cycle_Id: Optional[str] = None,
                             Process_Life_Cycle_id: Optional[str] = None, query_string:str=None,Hours: int = 12) -> Optional[Dict]:
        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)
        return {
            "타임스탬프_범위": {
                "기준시간": current_time,
                "과거시간": decreased_time,
                "미래시간": increased_time,
            },
            "이벤트": [
                {
                    "Kibana_Graph": "Bar",
                    "Description": "파일 시스템 Action 이벤트 총량 수치",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정
                            FILESYSTEM_BEHAVIOR_timeline_count_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
                },
                {
                    "Kibana_Graph": "Table",
                    "Description": "파일 시스템 최근 발생 이벤트",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정
                            FILESYSTEM_BEHAVIOR_timeline_recently_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> 파일 시스템 행위(Action -> Read, Write, Delete, Create ,,, )
                        "3": "key" -> 파일 명
                        "4": "key" -> ISO 포맷의 타임스탬프
                    '''
                }
            ]
        }

    def PROCESS_DASHBOARD(self, agent_id: Optional[str] = None, Root_Parent_Process_Life_Cycle_Id: Optional[str] = None,
                          Process_Life_Cycle_id: Optional[str] = None, query_string:str=None, Hours: int = 12) -> Optional[Dict]:
        current_time, increased_time, decreased_time = Set_Range_Time(Hours=Hours)



        t = self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            PROCESS_BEHAVIOR_Created_recently_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )

        return {
            "타임스탬프_범위": {
                "기준시간": current_time,
                "과거시간": decreased_time,
                "미래시간": increased_time,
            },
            "이벤트": [
                {
                    "Kibana_Graph": "Area",
                    "Description": "프로세스 생성 이벤트 빈도 수",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            PROCESS_BEHAVIOR_Created_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
                },
                {
                    "Kibana_Graph": "Table",
                    "Description": "프로세스 생성 디테일 이벤트 (생성한 프로세스 이름이나 커맨드라인 그리고 발생한 타임라인을 볼 수 있음",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            PROCESS_BEHAVIOR_Created_recently_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": '''
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> 생성된 프로세스 풀 네임,
                        "3": "key" -> 생성된 프로세스 커맨드 라인 값
                        "4": "key" -> ISO 포맷의 타임스탬프
                    '''
                },


                {
                    "Kibana_Graph": "Area",
                    "Description": "프로세스 종료 이벤트 빈도 수",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            PROCESS_BEHAVIOR_Terminated_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    )
                },
                {
                    "Kibana_Graph": "Table",
                    "Description": "프로세스 종료 디테일 이벤트 ( 종료한 프로세스 ID(root프로세스ID 아님)정보 + 타임스탬프 반환)",
                    "Log": self.query_to_elasticsearch_(
                        self.add_agent_id_or_root_id_into_filter(

                            increased_time, decreased_time,  # 시간 범위 설정

                            PROCESS_BEHAVIOR_Terminated_recently_EVENTS,  # 해당 차트에 대한 쿼리
                            agent_id,
                            Root_Parent_Process_Life_Cycle_Id,
                            Process_Life_Cycle_id,
                            query_string
                        )
                    ),
                    "Table_info": ''' 
                        // 엘라스틱서치 aggr 결과 파싱 정보
                        "0": "key" -> Root_Parent_Process_Life_Cycle_Id,
                        "1": "key" -> Process_Life_Cycle_id,
                        "2": "key" -> ISO 포맷의 타임스탬프
                    '''
                }

            ]
        }


    def query_to_elasticsearch_(self, q:dict)->Optional[Dict]:
        output_aggs = self.es.Query(index=self.INDEX_PATTERN, query=q, is_aggs=True)
        #output_aggs = output.get('aggregations', {})
        return output_aggs

    # 내부 함수처리

    def add_agent_id_or_root_id_into_filter(self,
                                            increased_time: str , decreased_time: str,

                                            query:dict,

                                            agent_id:str=None, Root_Parent_Process_Life_Cycle_Id:str=None, Process_Life_Cycle_id:Optional[str]=None, query_string:str=None,

                                            )->dict:

        copied_query = deepcopy(query)

        if agent_id:
            copied_query = Add_Agent_ID_filter(copied_query, agent_id)

        if Root_Parent_Process_Life_Cycle_Id:
            copied_query = Add_Root_Parent_Process_Life_Cycle_Id_filter(copied_query,Root_Parent_Process_Life_Cycle_Id)

        if Process_Life_Cycle_id:
            copied_query = Add_Process_Life_Cycle_id_filter(copied_query,Process_Life_Cycle_id)

        if query_string:
            copied_query = Add_Query_String_filter(copied_query, query_string)

        # 이벤트가 위치한 시간 범위 설정
        copied_query = Set_time_filter(copied_query, increased_time, decreased_time)

        return copied_query






'''i = kibanaDashboard(
    Elasticsearch(
        hosts=["http://localhost:9200"],
    )
)

r = i.REGISTRY_DASHBOARD()

print(
    r
)'''