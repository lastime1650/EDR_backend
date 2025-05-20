from typing import Optional, List, Tuple

from elasticsearch import Elasticsearch
from langchain_google_genai import ChatGoogleGenerativeAI

from enum import Enum
class Behavior_Types(Enum):

    # behavior
    ImageLoad = 0
    Registry = 1
    FileSystem = 2
    Network = 3
    Process_Created = 4
    Process_Terminated = 5


from enum import Enum



class OS(Enum):
    Windows = 1
    Linux = 2
    MacOS = 3

# 엘라스틱서치로부터 얻은 것을 기반으로 만든 프로세스 객체 ( "특정 프로세스"의 모든 행위가 저장된다. )
from EDR.servers.Elasticsearch import ElasticsearchAPI

class Process():
    def __init__(self, es: ElasticsearchAPI, INDEX_PATTERN:str="siem-*"):
        self.INDEX_PATTERN = "siem-edr-*"
        self.es = es

        self.Process_log = {
            "endpoint_info": {
                "Local_IP": "",
                "Mac_Address": "",

                "Agent_Id": "",
                "OS_Info": "",
            },
            "process_info": {

                "Process_Life_Cycle_Id" : "",
                "Parent_Process_Life_Cycle_Id": "",
                "Root_Parent_Process_Life_Cycle_Id": "",
                "Root_is_running_by_user": False,


                "Process_Created": {}, # 프로세스 생성
                "Process_Terminated": {} # 프로세스 종료
            },
            "behaviors": {
                "ImageLoad": [],
                "Registry": [],
                "FileSystem": [],
                "Network": [],
                "others": [], # 특수 다른 EDR 솔루션으로부터 얻은 정보
            },
        }

        # 이것들은 나중에 siem-security-event 인덱스 document에 활용됨
        self.common = {}
        self.categorical = {}

        # 운영체제
        self.OS:OS = OS.Windows

        # self.Response_Method = {} 차단 할 때 추가 예정

    def Add_to_Event(self, common_event:dict, categorical_event:dict, unique_event:dict):


        # Unique 이벤트의 동적인 key값(예: Process_Created) 에 있는 키로 검증하고 추가한다.
        #print(unique_event.keys())
        behavior_event = unique_event["process_behavior_events"]
        self.add_to_behavior_(behavior_event, common_event["Timestamp"])

        # 프로세스 정보 추가
        self.add_to_process_info_(common_event, categorical_event)

    # 내장 함수
    def add_to_process_info_(self, common_event:dict, categorical_event:dict):

        self.common = common_event
        self.categorical = categorical_event

        # 엔드포인트 정보
        self.Process_log["endpoint_info"]["Local_IP"] = common_event["Local_IP"]
        self.Process_log["endpoint_info"]["Mac_Address"] = common_event["Mac_Address"]

        self.Process_log["endpoint_info"]["Agent_Id"] = categorical_event["Agent_Id"]
        self.Process_log["endpoint_info"]["OS_Info"] = categorical_event["OS_info"]

        # 프로세스 정보
        self.Process_log["process_info"]["Process_Life_Cycle_Id"] = categorical_event["process_info"]["Process_Life_Cycle_Id"]
        self.Process_log["process_info"]["Parent_Process_Life_Cycle_Id"] = categorical_event["process_info"]["Parent_Process_Life_Cycle_Id"]
        self.Process_log["process_info"]["Root_Parent_Process_Life_Cycle_Id"] = categorical_event["process_info"]["Root_Parent_Process_Life_Cycle_Id"]
        self.Process_log["process_info"]["Root_is_running_by_user"] = categorical_event["process_info"]["Root_is_running_by_user"]
        # self.Process_log["process_info"]["Process_Created"]  # 프로세스 생성정보는 behavior 이벤트에서 추가한다.

    def add_to_behavior_(self, behavior_event:dict, Timestamp:str):


        #print( next( iter( behavior_event.keys() ) ) )
        current_behavior_key = next( iter( behavior_event.keys() ) ) # 첫번째 키 구하기

        # Timestamp 추가
        behavior_event[current_behavior_key]["Timestamp"] = Timestamp

        #print(behavior_event)
        # check behavior 프로세스 특정 행동 탐지
        if "Process_Created" == current_behavior_key:
            behavior_event['Process_Created']['event_name'] = "Process_Created"
            #behavior_event["Process_Created"]['analyzed_results'] = self.Analysis_Collector.Get_FILE_analysis_result( # 파일 분석 결과 추출
            #    sha256=behavior_event["Process_Created"]['ProcessSHA256'],
            #)
            self.Process_log["process_info"]["Process_Created"] = behavior_event["Process_Created"]
            print(f"EXE -> {behavior_event['Process_Created']['ImagePath']}")
        elif "Process_Terminated" == current_behavior_key:
            behavior_event['Process_Terminated']['event_name'] = "Process_Terminated"
            self.Process_log["process_info"]["Process_Terminated"] = behavior_event["Process_Terminated"]


        elif "registry" == current_behavior_key:
            self.add_behavior_Registry_(behavior_event["registry"])
        elif "file_system" == current_behavior_key:
            self.add_behavior_FileSystem_(behavior_event["file_system"])
        elif "network" == current_behavior_key:
            self.add_behavior_Network_(behavior_event["network"])
        elif "image_load" == current_behavior_key:
            self.add_behavior_ImageLoad_(behavior_event["image_load"])
        else:
            self.add_behavior_others_(behavior_event[current_behavior_key]) # 다른 것

    # 행위 축적 -> 분석 요청(특징 추출)
    def add_behavior_ImageLoad_(self, ImageEvent:dict):
        #ImageEvent['analyzed_results'] = self.Analysis_Collector.Get_FILE_analysis_result( # 파일 분석 결과 추출
        #    sha256=ImageEvent['ImageSHA256'],
        #)
        ImageEvent["event_name"] = "ImageLoad"
        self.Process_log["behaviors"]["ImageLoad"].append(ImageEvent)
    def add_behavior_Registry_(self, RegistryEvent:dict):
        RegistryEvent["event_name"] = "Registry"
        self.Process_log["behaviors"]["Registry"].append(RegistryEvent)
    def add_behavior_FileSystem_(self, FileSystemEvent:dict):
        #FileSystemEvent['analyzed_results'] = self.Analysis_Collector.Get_FILE_analysis_result(  # 파일 분석 결과 추출
        #    sha256=FileSystemEvent['ImageSHA256'],
        #)
        FileSystemEvent["event_name"] = "FileSystem"
        self.Process_log["behaviors"]["FileSystem"].append(FileSystemEvent)
    def add_behavior_Network_(self, NetworkEvent:dict):
        NetworkEvent["event_name"] = "Network"
        self.Process_log["behaviors"]["Network"].append(NetworkEvent)
    def add_behavior_others_(self, othersEvent:dict):
        othersEvent["event_name"] = "others"
        self.Process_log["behaviors"]["others"].append(othersEvent)

    # 차단 목록 추가 (필요없을 듯)
    def add_to_response_(self, response_method:dict):
        self.Response_Method = response_method
    
    #--
    
    # 마감 처리
    def Finalize(self):
        '''
            TODO: 전체 이벤트를 순서대로 ( Old -> New )정렬하여 한번에 저장.
        '''
        
        # ISO 문자열 타임스탬프 -> 시간 값 변환함수
        from datetime import datetime, timezone
        def parse_timestamp(event):
            
            if "Timestamp" not in event:
                return None
            
            ts_str = event["Timestamp"]
            dt = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            return dt.timestamp()  # float, 초 단위
        
        # 전체 behavior 이벤트 list 하나로 결합 후 Old -> New 정렬
        # 1. 프로세스 생성 타임스탬프
        # 2. 프로세스 종료 타임스탬프
        # 3. 프로세스 이벤트 다른 타입 ( Filesystem, Others(자식 생성 등등 사전에 정의되지 않은 불투명 이벤트), Registry, ImageLoad, Network )
        behavior_events = []
        if "Timestamp" in self.Process_log["process_info"]["Process_Terminated"]:
            behavior_events.extend([self.Process_log["process_info"]["Process_Terminated"]])
        
        if "Timestamp" in self.Process_log["process_info"]["Process_Created"]:
            behavior_events.extend([self.Process_log["process_info"]["Process_Created"]])
        
        
        behavior_events += self.Process_log["behaviors"]["Registry"] + self.Process_log["behaviors"]["FileSystem"] + self.Process_log["behaviors"]["Network"] + self.Process_log["behaviors"]["ImageLoad"] + self.Process_log["behaviors"]["others"]
        
        result =  sorted(behavior_events, key=lambda x: parse_timestamp(x))
        
        self.Sorted_Events = result
        

    # 수 많은 이벤트에 대한 집계 쿼리 수행 -> 연관분석에 활용될 수 있음
    
    def output_aggregation_(self)->list[dict]:

        from EDR.process_.aggs_queries_ import Output___Process_Behavior_Aggregation
        
        output:list[dict] = Output___Process_Behavior_Aggregation(
            ProcessCycleId=self.Process_log["process_info"]["Process_Life_Cycle_Id"],
            es=self.es,
            
        )
        
        output.append(
            {
                "imageload": self.Process_log["behaviors"]["ImageLoad"]
            }
        )
        
        print(f"--> aggr -> output -> \n{output}")
        return output
    #--


    # 정보 반환 함수
    def Output_Process_Info(self)->dict:

        process_log = {
            "process_event": self.Process_log,
            "behavior_timeline": self.Sorted_Events
        }
        
        
        return process_log
    def Output_Root_Parent_Process_Life_Cycle_Id(self)->str:
        return self.Process_log["process_info"]["Root_Parent_Process_Life_Cycle_Id"]
    def Output_Parent_Process_Life_Cycle_Id(self)->str:
        return self.Process_log["process_info"]["Parent_Process_Life_Cycle_Id"]
    def Output_Process_Life_Cycle_Id(self)->str:
        return self.Process_log["process_info"]["Process_Life_Cycle_Id"]