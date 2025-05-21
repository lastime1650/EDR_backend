from typing import Optional

from elasticsearch import Elasticsearch

class ElasticsearchAPI():
    def __init__(self, host: str, port: int):
        self.es = Elasticsearch(hosts=[f"http://{host}:{port}"])
    
    
        
    def Query(self, query:dict, index:str, is_aggs:bool=False)->Optional[any]:
        result = self.es.search(
            index=index,
            body=query
        )
        #print(result)
        if not is_aggs:
            if len(result["hits"]["hits"]) > 0:
                return result["hits"]["hits"]
            else:
                return None 
        else:
            return result["aggregations"]
        
    def EQL_Query(self, eql_query:str, dsl_filter:Optional[dict], index:str)->Optional[list]:
        
        #print(f"EQL Query -> {eql_query} // dsl_filter -> {dsl_filter} // index -> {index}")
        
        
        # dsl_filter 입력 구조는 최상위 filter key는 필요없음 search시 자동으로 붙음
        
        result = self.es.eql.search(
            query=eql_query,
            
            filter=dsl_filter,
            
            index=index,
        )
        
        '''
        {
            "hits":{
                "events":[_source... 결과들] -------------> hits가 아닌 [hits][events]임. ( es.search 의 [hits][hits]와 다름)
            }
        }
        '''
        
        # result 파싱

        if len(result["hits"]["events"]) == 0:
            return None
        else:
            return result["hits"]["events"]
        
      
    
    def Check_Exist_Index_Template(self, index_name:str)->bool:
        return self.es.indices.exists_index_template(index=index_name)
    
    # - 유틸
    

'''es = ElasticsearchAPI(
    host = "192.168.0.1",
    port = 9200
)

a = es.Query(
    query={
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
        },
    index="siem-edr-*",
    is_aggs=True
)

print(a)'''