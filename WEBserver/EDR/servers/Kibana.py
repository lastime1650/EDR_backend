from EDR.servers.Elasticsearch import ElasticsearchAPI
class KibanaAPI():
    def __init__(self, host: str, port: int, es: ElasticsearchAPI):
        self.HTTP_connection = f"http://{host}:{port}"
        
        from EDR.servers.kibana__Utility.Dashboard import kibanaDashboard
        self.SearchDashboard = kibanaDashboard(
            es=es
            ) # 대시보드 쿼리용
    
    # 루시네 언어 쿼리 --> URL 
    def Get_Iframe(self, lucene_query:str):
        lucene_query = lucene_query.replace("'","%27").replace('"',"%22")
        return f"&_a=(filters:!(),query:(language:lucene,query:%27{lucene_query}%27))"
    
    