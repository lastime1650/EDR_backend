# 엘라스틱서치 분석 결과를 요청해서 가져오는 클래스
from typing import Optional, List, Tuple
import json

from EDR.servers.Elasticsearch import ElasticsearchAPI

from enum import Enum
class analysis_type(Enum):
    file = 1
    network = 2

class AnalysisServerTool():
    def __init__(self, es: ElasticsearchAPI, INDEX_PATTERN:str="share-analysis-*"):
        self.es = es
        self.INDEX_PATTERN = INDEX_PATTERN
        
    def Get_File_Analysis_Result(self, sha256:str)->Optional[dict]:
        query = self.make_FILE_query(sha256)
        return self.get_analysis_result(
                    query,
                    analysis_type.file
                )
    
    def Get_Network_Analysis_Result(self, remoteip:str)->Optional[dict]:
        query = self.make_NETWORK_query(remoteip)
        return self.get_analysis_result(
                    query,
                    analysis_type.network
                )
    
    def make_FILE_query(self, sha256:str)->dict:
        return {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "term": {
                                "types.file.sha256": sha256
                            }
                        }
                    ]
                }
            },
            "size": 1,
            "_source": True
        }
    
    def make_NETWORK_query(self, remoteip:str)->dict:
        return {
            "query": {
                "bool": {
                    "filter": [
                        {
                            "term": {
                                "types.network.remoteip": remoteip
                            }
                        }
                    ]
                }
            },
            "size": 1,
            "_source": True
        }
        
        
    # Elasticsearch 쿼리 요청
    def get_analysis_result(self, query:dict, analysis_type:analysis_type)->Optional[dict]:
        
        result = self.es.Query(query=query, index=self.INDEX_PATTERN, is_aggs=False)
        if result:
            
            if analysis_type == analysis_type.file:
                return result[0]["_source"]["types"]["file"]
            elif analysis_type == analysis_type.network:
                return result[0]["_source"]["types"]["network"]
            else:
                return None
        else:
            return None