from elasticsearch import Elasticsearch
from typing import Union, Optional
import threading

# 
# - edr 일 때, 
# edr.llm_result.type : process -> 프로세스 분석 결과
# edr.llm_result.type : tree -> 프로세스 트리 분석 결과

index_patterns = "llm-analysis-*"
index_name = "llm-analysis-server"
template_name = "llm-analysis-index-template"
template = {

    "index_patterns": "llm-analysis-*",

    "priority":       297,

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
                "Timestamp": {"type": "date"},
                "edr": {
                    "properties": {
                        "llm_result": {
                            "properties": {
                                #"result": { #-> 정의는 안함 값이 put하면서 들어감
                                #    "properties": {
                                    
                                         # tree의 경우에만
                                 #       "tree_node_depth": {"type": "integer"}, # Tree 노드의 깊이
                                 #       "tree_node_count": {"type": "integer"}, # Tree 노드의 개수
                                        
                                  #  }
                                
                                
                                #}
                            }
                        },
                        
                        
                        
                        
                        # 불변의 일방향 해시값을 통해서 "동일한 EXE"를 사용하여 틀린 분석 값으로 분석결과를 나타내지 않도록 하기 위해 root_parent, parent, self 로 분할 매치하도록 필드 3분할 함
                        "root_parent_sha256": {"type": "keyword"}, # self의 root 파일 SHA256 ( self와 동일 할 수 있음 )
                        "parent_sha256":{"type":"keyword"}, # self의 parent 파일 SHA256 ( self와 동일 할 수 있음 )
                        "self_sha256": {"type": "keyword"}, # self 파일 SHA256
                        "self_sha256_filesize": {"type": "long"}, # self 파일 크기
                    }
                }
            }
        }
    }
}

from Utility.timestamper import Get_Current_Time

from enum import Enum

class Behavior_ElasticSearch():
    def __init__(self, elastichost:str, elasticport:int, INDEX_PATTERN:str="llm-analysis-*"):
        self.es = Elasticsearch(hosts=[f"http://{elastichost}:{elasticport}"])
        self.INDEX_PATTERN = INDEX_PATTERN

        self.mutex_ = threading.Lock()

        # 템플릿 존재 체크 없으면 생성
        self.check_template_exist_(is_create_if_none=True)

        pass
    
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
    
    
    def Add_EDR_Analysis(
        self, 
        llm_result:dict, 
        self_sha256:str, parent_sha256:str, root_parent_sha256:str,
        self_filesize:int,
        is_append:bool=False # ==> True: 추가 , False: 기존 있는 경우 Add작업 안함 -> None반환
        ):
        
        # 데이터 삽입
            self.put_(
                document={
                    "Timestamp":Get_Current_Time(),
                    "edr":{
                        "llm_result": {
                            "result": llm_result
                        },
                        "root_parent_sha256": root_parent_sha256, # self의 root 파일 SHA256 ( self와 동일 할 수 있음 )
                        "parent_sha256":parent_sha256, # self의 parent 파일 SHA256 ( self와 동일 할 수 있음 )
                        "self_sha256": self_sha256,
                        "self_sha256_filesize": self_filesize,
                    }
                }
            )
        
            
    def put_(self, document:dict ):
        from datetime import datetime

        dt = datetime.strptime(Get_Current_Time(), "%Y-%m-%dT%H:%M:%S.%fZ")
        date_only = dt.strftime("%Y.%m.%d")

        self.es.index( # 전송
            index=f"{index_name}-{date_only}",
            document=document,
        )
    
    
    # 프로세스 트리 전체에 대한 결과 쿼리
    def get_by_tree(self, self_sha256:str, parent_sha256:str, root_parent_sha256:str, tree_node_depth:int, tree_node_count:int)->Optional[dict]:
        
        # count는 변수가 있어서 보류
        
        
        output = self.es.search(
            index=index_patterns,
            body={
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "term": {
                                    "edr.root_parent_sha256": root_parent_sha256,
                                    
                                }
                            },
                            {
                                "term": {
                                    "edr.parent_sha256": parent_sha256,
                                }
                            },
                            {
                                "term": {
                                    "edr.self_sha256": self_sha256,
                                }
                            },
                            {
                                "term": {
                                    "edr.llm_result.result.tree_node_depth": tree_node_depth
                                }
                            },
                            #{
                            #    "term": {
                            #        "edr.llm_result.result.tree_node_count": tree_node_count
                             #   }
                            #}
                            
                        ]
                    }
                },
                "size": 1,
                "_source": True
            }
        )
        
        if len(output["hits"]["hits"]) > 0:
            return output["hits"]["hits"][0]["_source"]
        else:
            return None
        
    def get_by_sha256(self, process_sha256:str, parent_sha256:str)->Optional[list[dict]]:
        
        output = self.es.search(
            index=index_patterns,
            body={
                    "query": {
                        "bool": {
                            "filter": [
                                {
                                    "term": {
                                        "edr.self_sha256": process_sha256
                                    }
                                },
                                {
                                    "term": {
                                        "edr.parent_sha256": parent_sha256
                                    }
                                }
                            ]
                        }
                    },
                    "size": 1000,
                    "_source": True
                } 
        )
        
        if len(output["hits"]["hits"]) > 0:
            return  [ dict(hit["_source"])["edr"] for hit in output["hits"]["hits"] ]
        else:
            return None