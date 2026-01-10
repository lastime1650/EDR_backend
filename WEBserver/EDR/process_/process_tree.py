from typing import Optional, Tuple


from EDR.process_.process_instance_ import Process
from EDR.servers.Elasticsearch import ElasticsearchAPI

class Process_Tree_Maker():
    def __init__(self, es: ElasticsearchAPI, INDEX_PATTERN:str="siem-*", need_analysis_results:bool=False):
        self.es = es
        self.INDEX_PATTERN = INDEX_PATTERN
        
        # 프로세스 Tree 수집시 분석 결과 포함 여부 ( 결과 포함 시,,,,, Blocking 시간이 길어짐 )
        self.need_analysis_results = need_analysis_results

    def Create_Process_Tree(self, Root_Process_Life_Cycle_Id: str)->Tuple[ Optional[dict], Optional[str] ]:
        
        Root_Process = self.process_scan_____(Root_Process_Life_Cycle_Id)
        if not Root_Process:
            return None, None
        
        tree = {
            "self": Root_Process.Output_Process_Info(),
            "child": [],
            "_node_depth": {"key": 0}, # Tree 노드의 깊이
            "_node_count": {"key": 1}, # Tree 노드의 개수
        }
        
        self.loop_find_process_tree_from_root_(
            my_Process_Life_Cycle_Id=Root_Process_Life_Cycle_Id,
            child_list=tree["child"],
            
            node_depth_field=tree["_node_depth"],
            node_count_field=tree["_node_count"],
        )
        
        #print(f'[1/2]트리----> 깊이:{tree["_node_depth"]["key"]}, 개수:{tree["_node_count"]["key"]}')
        self.Get_Node_Counting(tree) # 재 초기화 후 구하기
        #print(f'[2/2]트리----> 깊이:{tree["_node_depth"]["key"]}, 개수:{tree["_node_count"]["key"]}')
        
        
        
        # TREE 기반 Mermaid 그래프 생성
        from WebManagement.Mermaid import Mermaid_Graph_Maker
        mermaid_graph_maker = Mermaid_Graph_Maker()
        
        # root 시작 노드
        s, d = mermaid_graph_maker.Add_New_Node(
            "시작",
            "Tree 프로세스 생성 흐름"
        )
        
        self.parsing_root_process_tree_(tree, s, mermaid_graph_maker)
        result_mermaid_graph = mermaid_graph_maker.Complete_Graph()# 이 후... Complete_Graph() -> ret -> mermaid_graph_maker.Mermaid_graph_string -> 에는 그래프가 완성됨
        
        return tree, result_mermaid_graph
    
    
    
    # 내부 메서드
    def loop_find_process_tree_from_root_(self, my_Process_Life_Cycle_Id:str, child_list: list, node_depth_field:dict, node_count_field:dict):
        current_Timestamp: Optional[str] = None
        size_chunk = 100
        while True:
            # 반복
            # 해당 프로세스 이벤트에서 "자식"이벤트가 있는 지 확인
            q = {
                "query": {
                    "bool": {
                        "filter": [
                            {
                                "term": {
                                    "categorical.process_info.Process_Life_Cycle_Id": my_Process_Life_Cycle_Id
                                }
                            },
                            {
                                "exists": {
                                    "field": "unique.process_behavior_events.Child_Process_Created"
                                }
                            },
                            {
                                "range": {
                                    "common.Timestamp": {
                                        "gt": current_Timestamp
                                    }
                                }
                            }

                        ],
                    }
                },
                "sort": [
                    # Timestamp 오름차순 정렬은 필요없는 듯
                    {'common.Timestamp': {"order": "asc"}}  # 제일 오래된 순 부터
                ],
                "size": size_chunk,
                "_source": [
                    "unique.process_behavior_events.Child_Process_Created",
                    "common.Timestamp",
                    "categorical.process_info"
                ]
            }
            hits = self.es.Query(q, self.INDEX_PATTERN, is_aggs=False)
            if hits == None:
                print("조회 실패(새로운 로그가 없음)")
                break
            
            # 노드 depth 증가 
            node_depth_field["key"] += 1
            
            
            sources = self.make_sources_(hits)

            for source in sources:
                current_Timestamp = source["common"]["Timestamp"]
                child_process_event = source["unique"]["process_behavior_events"]["Child_Process_Created"]
                Child_Process_Life_Cycle_Id = child_process_event["Child_Process_Life_Cycle_Id"]
                output_process = self.process_scan_____(
                    Child_Process_Life_Cycle_Id
                )

                # 프로세스 자식 트리 정보 생성
                current_child = {
                    "self": output_process.Output_Process_Info(),
                    "child": []
                }
                
                # 노드 개수 증가
                node_count_field["key"] += 1
                
                self.loop_find_process_tree_from_root_(Child_Process_Life_Cycle_Id, current_child["child"], node_depth_field, node_count_field)

                child_list.append(current_child) # 프로세스 자식 트리 정보 생성


                #return # <- 임시
    
    # 노드 탐색 # 
    def Get_Node_Counting(self, tree:dict, child_field_name="child"):
        
        tree["_node_depth"]["key"] = 0
        tree["_node_count"]["key"] = 1
        
        self.get_node_counting_recursive(child_list=tree[child_field_name], node_depth_field=tree["_node_depth"], node_count_field=tree["_node_count"])
        
        return tree
        
    
    def get_node_counting_recursive(self, child_list:list, node_depth_field:dict, node_count_field:dict, child_field_name="child"):
        
        if len(child_list) == 0:
            return
        
        node_depth_field["key"] += 1 # 깊이 카운트
        
        for child in child_list:
            
            node_count_field["key"] += 1 # 개수 카운트
            
            self.get_node_counting_recursive(child[child_field_name], node_depth_field, node_count_field)
    #############
    
    def process_scan_____( self, Process_Life_Cycle_Id: str)->Optional[Process]:
        # 프로세스 당 ,, 이벤트가 상당히 많기 때문에, 타임스탬프 기반으로 반복 쿼리 (최신일 때 까지)
        # 이 작업은 병렬 처리를 하지 않는다. ( 오로지 순차적 실행 )

        process_instance = Process(self.es, self.INDEX_PATTERN)

        Start_Timestamp: Optional[str] = None
        current_timestamp: Optional[str] = None
        size_chunk = 2000
        is_loop_break = False
        is_first_loop = True
        while True:
            if is_loop_break:
                break
            # 쿼리 설명
            '''
                1. size_chunk 이벤트 개수 범위
                2. current_timestamp -> 조회결과마다 가장 최근의 타임스탬프를 Update하여 반복 쿼리용 ( 마지막엔 프로세스 종료 시간이 된다 ) 
                3. Start_Timestamp -> 최초 조회 시간 ( 프로세스 생성 시간이 된다 )
                4. 설명: categorical::Process_Life_Cycle_Id이 일치한 하나의 프로세스에 대한 행위를 모두 가져오는 것임.
            '''
            query = {
                "query": {
                    "bool": {

                        # filter 절은 점수 계산을 하지 않아 must보다 약간 더 효율적일 수 있습니다.
                        # 두 조건을 모두 만족해야 하는 경우 사용합니다.
                        "filter": [
                            {
                                "term": {
                                    "categorical.process_info.Process_Life_Cycle_Id": Process_Life_Cycle_Id
                                }
                            },

                            {
                                "range": {
                                    "common.Timestamp": {
                                        "gt": current_timestamp
                                    }
                                }
                            },
                        ]

                    },
                },
                "sort": [
                    # Timestamp 오름차순 정렬은 필수입니다. 이 방식의 페이지네이션 기준이기 때문입니다.
                    {'common.Timestamp': {"order": "asc"}}  # 제일 오래된 순 부터
                ],
                "size": size_chunk,
                "_source": {
                    "includes": [
                        "common",
                        "categorical",
                        "unique.process_behavior_events"
                    ],
                }
            }
            hits = self.es.Query(query, self.INDEX_PATTERN, is_aggs=False)
            if hits == None:
                print("조회 실패(새로운 로그가 없음)")
                if is_first_loop: # 성공적으로 Process 정보 얻었는 지 판별용
                    return None
                else:
                    break
            else:
                is_first_loop = False 
                
            sources = self.make_sources_(hits)

            for event in sources:
                if "common" not in event or "categorical" not in event:
                    continue
                elif "unique" not in event:
                    is_loop_break = True
                    break
                # print(event)
                common_event = event["common"]
                unique_event = event["unique"]
                categorical_event = event["categorical"]

                current_timestamp = common_event["Timestamp"]  # 시간 업데이트

                # 시작 시간 설정
                if Start_Timestamp == None:
                    Start_Timestamp = current_timestamp

                # 프로세스 인스턴스에 담기
                process_instance.Add_to_Event(common_event, categorical_event, unique_event, self.need_analysis_results)


        # 마감처리
        process_instance.Finalize()
        
        # 타임스탬프 순 이벤트 출력
        #print( process_instance.Sorted_Events )
        
        # 테스트 물리 저장
        import json
        events = process_instance.Sorted_Events
        with open('test.json', 'w') as f:
            json.dump(events, f)
        
        return process_instance














    # 유틸 -> 엘라스틱서치 _source 유효한 field일 때 검증하여 반환하는 것
    def make_sources_(self, hits:any)->list[dict]: # 3
        output_sources_:list[dict] = []

        for hit in hits:
            one_event = {}
            for key, value in dict(hit["_source"]).items():
                if key in ["common", "categorical", "unique"]:
                    one_event[key] = value

            output_sources_.append(one_event)

        return output_sources_
    
    
    # 완성된 Tree -> Mermaid 그래프 레이블 생성
    def make_mermaid_node_label_(self, process_info:dict)->str:
        # 프로세스 트리에서 노드 레이블을 어떻게 표현할 것인가?
        # 노드 레이블은 프로세스 정보에 대한 정보를 담고 있어야 한다.
        process_info = process_info["self"]["process_event"] # 프로세스 정보가 담긴 Field
        ImagePath = str(process_info['process_info']['Process_Created']['ImagePath']).split('\\')[-1]
        timestamp = str(process_info['process_info']['Process_Created']['Timestamp'])
        node_label = f"{ImagePath}\n{process_info['process_info']['Process_Life_Cycle_Id']}\n타임스탬프:{timestamp}"#\n{process_info['process_info']['Process_Created']['ImagePath']}"
        return node_label


    from WebManagement.Mermaid import Mermaid_Graph_Maker
    def parsing_root_process_tree_(self, process_info:dict, src_node_id:str, mermaid_instance:Mermaid_Graph_Maker):
    
        #current_process_cycle_id = process_info["info"]["process_info"]["Process_Life_Cycle_Id"]

        # 자식 프로세스 mermaid node 추가
        current_process_cycle_node_id = mermaid_instance.Connect_Node(
            self.make_mermaid_node_label_(process_info=process_info),
            src_node_id_parm=src_node_id, dest_color= "#33FFFF"
        )

        # 행위 추가
        """mermaid_instance.Connect_Node(
            "1\n2\n3\n4\n5",
            src_node_id_parm=current_process_cycle_node_id
        )
        mermaid_instance.Connect_Node(
            "1\n2\n3\n4\n5",
            src_node_id_parm=current_process_cycle_node_id
        )
        mermaid_instance.Connect_Node(
            "1\n2\n3\n4\n5",
            src_node_id_parm=current_process_cycle_node_id
        )
        mermaid_instance.Connect_Node(
            "1\n2\n3\n4\n5",
            src_node_id_parm=current_process_cycle_node_id
        )"""


        for child in process_info["child"]:
            self.parsing_root_process_tree_(child, current_process_cycle_node_id, mermaid_instance) # 재귀 함수