# 분석결과 -> ElasticSearch 에 저장
# 그전에 확인 작업 진행한다.
import threading
from typing import Union, Optional

from elasticsearch import Elasticsearch

from Utility.timestamper import Get_Current_Time

index_patterns = "share-analysis-*"
index_name = "share-analysis-server"
template_name = "share-analysis-server-index-template"
template = {

    "index_patterns": "share-analysis-*",

    "priority":       299,

    "template": {
        "settings": {
            "number_of_shards":   1,
            "number_of_replicas": 0,
            "mapping": {
                      "total_fields": {
                        "limit": 2000  # 여기서 필드 개수 제한 설정 (동적 필드 설정 시 너무 많으면 오류 발생하는 점을 해소하기 위한 방법)
                      }
                    }
        },
        "mappings": {
            "properties": {

                # 상위 키 2개

                # 1. 타임스탬프
                # 2. 파일 타입별 키

                "Start_timestamp": { # 인덱스 생성 시간
                    "type": "date"
                },

                "Last_timestamp": { # 최근 업데이트 시간
                    "type": "date"
                },

                # 파일 유형
                "types": {
                    "properties": {
                        "file" : {
                            "properties" : {

                                "sha256": {
                                    "type":"keyword"
                                },
                                "file_size" : {
                                    "type": "long"
                                },
                                #"analysis": {
                                #    "properties" : {
                                #        # 여기부터는 동적으로 필드가 추가될 수 있음
                                 #   }
                                #}
                            }
                        },
                        # 네트워크 유형
                        "network": {
                            "properties" : {
                                "remoteip": {
                                    "type":"keyword"
                                },
                                #"analysis": {
                                #    "properties" : {
                                #        # 여기부터는 동적으로 필드가 추가될 수 있음
                                #    }
                                #}
                            }
                        }
                    }
                }

            }
        }
    }
}



class Analysis_ElasticSearch():
    def __init__(self, elastichost:str, elasticport:int, INDEX_PATTERN:str="share-analysis-*"):
        self.es = Elasticsearch(hosts=[f"http://{elastichost}:{elasticport}"])
        self.INDEX_PATTERN = INDEX_PATTERN

        self.mutex_ = threading.Lock()

        # 템플릿 존재 체크 없으면 생성
        self.check_template_exist_(is_create_if_none=True)

        pass

    # -
    # 한번에 삽입
    def Add_FILE_(self, sha256:str, file_size:int, extra:Union[dict,list],timestamp:str=None):

        # 현재 시간 구하기
        if not timestamp:
            timestamp = Get_Current_Time()

        # 여기부터는 중복체크하고, 중복이 아니면 데이터 추가.
        '''
            중복체크 방법

            1. sha256이 ES에 없는가? -> 추가
            2. sha256이 ES에 있는가? -> 중복체크 진행
                2.1 'analysis' 필드에서 값이 없는가? -> Update(새로)
                2.2 'analysis' 필드에서 값이 있는가? -> analysis 파싱하여 없는 필드만 추가 Update
        '''

        if self.is_document_exist_from_FILE(
            sha256=sha256,
            current_analysis_list=extra,
            if_update=False # 새로운 스크립트나 변경사항이 있으면 추가할지 여부
        ):
            # 이미 존재하면 추가 안해도됨
            return

        self.add_(
            analysis_result={
                "file": {
                    "sha256": sha256,
                    "file_size": file_size,
                    "analysis": extra
                }
            },
            start_timestamp=timestamp,  # 최초 생성 타임스탬프
        )

    def Add_NETWORK_(self, remoteip:str, extra:Union[dict,list],timestamp:str=None):
        # 현재 시간 구하기
        if not timestamp:
            timestamp = Get_Current_Time()

        self.add_(
            analysis_result={
                "network": {
                    "remoteip": remoteip,
                    "analysis": extra
                }
            },
            start_timestamp=timestamp, # 최초 생성 타임스탬프
        )

    def is_document_exist_from_FILE(self, sha256:str, current_analysis_list:Union[dict,list]=None, if_update:bool=False )->bool:
        q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "types.file.sha256": sha256
                            }
                        }
                    ]
                }
            },
            "size": 2,
            "_source": True
        }
        response = self.es.search(index=self.INDEX_PATTERN, body=q)
        hits = response.get('hits', {})
        if len(hits['hits']) == 0:
            return False
        else:

            if (if_update) and (current_analysis_list):

                # 업데이트 할지 체크.
                one_data = hits['hits'][0]
                index_name = one_data['_index']
                document_id = one_data['_id']

                analysis_dict_list:list[dict] = one_data["_source"]["types"]["file"]["analysis"]

                original = [  script_name for analyze_script_result in analysis_dict_list for script_name in  analyze_script_result ]
                new = [  script_name for analyze_script_result in current_analysis_list for script_name in  analyze_script_result ]

                for script_name in original:
                    not_in_here = True
                    for new_script_name in new:
                        if script_name == new_script_name:
                            not_in_here = False
                            break

                    # 기존과 다른 스크립트 모듈이 있으면 전체 업데이트
                    if not_in_here:
                        self.update_doc(
                            index_name=index_name,
                            document_id=document_id,
                            update_analysis={
                                                "types": {
                                                    "file": {
                                                        "analysis": current_analysis_list
                                                    }
                                                }
                                            }
                        )
                        break


            return True
        
    def is_document_exist_from_NETWORK(self, remoteip:str, current_analysis_list:Union[dict,list]=None, if_update:bool=False )->bool:
        q = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "types.network.remoteip": remoteip
                            }
                        }
                    ]
                }
            },
            "size": 2,
            "_source": True
        }
        response = self.es.search(index=self.INDEX_PATTERN, body=q)
        hits = response.get('hits', {})
        if len(hits['hits']) == 0:
            return False
        else:

            if (if_update) and (current_analysis_list):

                # 업데이트 할지 체크.
                one_data = hits['hits'][0]
                index_name = one_data['_index']
                document_id = one_data['_id']

                analysis_dict_list:list[dict] = one_data["_source"]["types"]["network"]["analysis"]

                original = [  script_name for analyze_script_result in analysis_dict_list for script_name in  analyze_script_result ]
                new = [  script_name for analyze_script_result in current_analysis_list for script_name in  analyze_script_result ]

                for script_name in original:
                    not_in_here = True
                    for new_script_name in new:
                        if script_name == new_script_name:
                            not_in_here = False
                            break

                    # 기존과 다른 스크립트 모듈이 있으면 전체 업데이트
                    if not_in_here:
                        self.update_doc(
                            index_name=index_name,
                            document_id=document_id,
                            update_analysis={
                                                "types": {
                                                    "network": {
                                                        "analysis": current_analysis_list
                                                    }
                                                }
                                            }
                        )
                        break


            return True

    def update_doc(self, index_name:str, document_id:str, update_analysis:dict):
        # 문서 업데이트
        # 업데이트 기준?
        # 상위 -> types -> file -> analysis [LIST] 에서 처음보는 스크립트 모듈 닉네임인경우 추가하는 형태.
        self.update_to_elasticsearch_(
            index_name=index_name,
            document_id=document_id,
            update_analysis=update_analysis
        )


    def add_(self, analysis_result:dict, start_timestamp:str=None, update_timestamp:str=None):

        already_doc = self.create_document_(analysis_result, start_timestamp, update_timestamp)

        es_timestamp = ""
        if start_timestamp:
            es_timestamp = start_timestamp
        elif update_timestamp:
            es_timestamp = update_timestamp
        else:
            es_timestamp = Get_Current_Time()

        self.send_to_elasticsearch_(already_doc, es_timestamp)



    # 내장 함수


    def create_document_(self, original:dict, start_timestamp:str=None, update_timestamp:str=None)->dict:
        output = {
            "types": original
        }

        if start_timestamp:
            output["Start_timestamp"] = start_timestamp
        if update_timestamp:
            output["Last_timestamp"] = update_timestamp

        return output

    def send_to_elasticsearch_(self, document:dict, timestamp:str):
        from datetime import datetime

        dt = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")
        date_only = dt.strftime("%Y.%m.%d")

        self.es.index( # 전송
            index=f"{index_name}-{date_only}",
            document=document,
        )

    def update_to_elasticsearch_(self, index_name:str, document_id:str, update_analysis:dict):
        self.es.update(
            index= index_name,
            id=document_id,
            doc = update_analysis
        )

    def check_template_exist_(self, is_create_if_none:bool=False):
        if self.es.indices.exists_index_template(name=template_name):
            return True
        else:
            if is_create_if_none:
                # 인덱스 생성
                self.es.indices.put_index_template(
                    name=template_name,
                    body=template
                )

