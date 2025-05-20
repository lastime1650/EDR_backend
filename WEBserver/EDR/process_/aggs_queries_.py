
def Network__aggregation_query____(process_cycle_id:str)->dict:
    return {
        "query": {
            "bool": {
                "filter": [
                    {
                        "term": {
                            "categorical.process_info.Process_Life_Cycle_Id": process_cycle_id
                        }
                    }
                ]
            }
        },
        "aggs": {
            "network_event_aggregation": {  # 원격지 IP 로 나눔 (집계 )
                 "terms":{
                    "field": "unique.process_behavior_events.network.RemoteIp",
                    "size": 5
                },
                "aggs": {
                    "ports": {
                        "terms": { # 여러 원격지 포트로 나눔 (집계 )
                            "field": "unique.process_behavior_events.network.RemotePort",
                            "size": 5
                        },
                        "aggs": {
                            "protocols":{ # 여러 프로토콜로 나눔 (집계 )
                                "terms": {
                                    "field": "unique.process_behavior_events.network.Protocol",
                                    "size": 5
                                },
                                "aggs": {
                                    "bounds": { # In , Out 바운드로 나눔 (집계 )
                                        "terms": {
                                            "field": "unique.process_behavior_events.network.Direction",
                                            "size": 2
                                        },
                                        "aggs": {
                                            "PacketDataResultSum": { # 패킷 크기 다 더함 (집계
                                                "sum": {
                                                    "field": "unique.process_behavior_events.network.PacketSize"
                                                }
                                            },
                                            "earlist_timestamp": {  # 설정된 집계에 포함된 타임스탬프내 최초, 최근 타임스탬프 구분
                                                "min": {
                                                    "field": "common.Timestamp"  # Old
                                                }
                                            },
                                            "latest_timestamp": {
                                                "max": {
                                                    "field": "common.Timestamp"  # Latest
                                                }
                                            }
                                        },

                                    }
                                }
                            }
                        }

                    },
                    "representative_geoip": {
                        "top_hits": {
                            "size": 1,  # 각 고유 IP당 하나의 대표 문서만 가져옴
                            "_source": {
                                # 필요한 geoip 필드만 선택적으로 가져옴
                                "includes": [
                                    "unique.process_behavior_events.network.geoip"
                                ]
                            }
                        }
                    }
                },

            },

        },
        "size": 0,
    }
    
    
##


def FileSystem__aggregation_query____(process_cycle_id:str)->dict:
    return {
        "query": {
            "bool": {
                "filter": [
                    {
                        "term": {
                            "categorical.process_info.Process_Life_Cycle_Id": process_cycle_id
                        }
                    }
                ]
            }
        },
        "aggs": {
            "file_system_event_aggregation": {  # 파일 경로 로 나눔 (집계 )
                "composite": {
                    "size": 1000,
                    "sources": [
                        # -- 파일 경로 + 크기 조합
                        # 파일 경로
                        { "file_path": { "terms": { "field": "unique.process_behavior_events.file_system.FilePath.keyword" } } },
                        # 파일 크기
                        { "file_size": { "terms": { "field": "unique.process_behavior_events.file_system.FileSize" } } },
                        # 파일 행위
                        { "file_action": { "terms": { "field": "unique.process_behavior_events.file_system.Action" } } },
                    ]
                },
                "aggs": {
                  "max_timestamp": {
                    "max": {
                      "field": "common.Timestamp"
                    }
                  },
                  "bucket_order": {
                    "bucket_sort": {
                      "sort": [
                          {"_count": {"order": "desc"}},
                            { "max_timestamp": { "order": "desc" } }
                      ],
                        "size": 100
                    }
                  },
                }

            }
        },
        "size": 0,
    }


##

def Registry__aggregation_query____(process_cycle_id:str)->dict:
    return {
        "query": {
            "bool": {
                "filter": [
                    {
                        "term": {
                            "categorical.process_info.Process_Life_Cycle_Id": process_cycle_id
                        }
                    }
                ]
            }
        },
        "aggs": {
            "registry_event_aggregation": {  # 파일 경로 로 나눔 (집계 )
                "composite": {
                    "size": 10000,
                    "sources": [
                        # -- 파일 경로 + 크기 조합
                        # 파일 경로
                        { "RegistryKey": { "terms": { "field": "unique.process_behavior_events.registry.RegistryKey" } } },
                        # 파일 크기
                        { "RegistryObjectName": { "terms": { "field": "unique.process_behavior_events.registry.RegistryObjectName" } } }
                    ]
                },
                "aggs": {
                    "max_timestamp": {
                        "max": {
                            "field": "common.Timestamp"
                        }
                    },
                    "bucket_order": {
                        "bucket_sort": {
                            "sort": [
                                {"_count": {"order": "desc"}},
                                {"max_timestamp": {"order": "desc"}}
                            ],
                            "size": 200
                        },

                    },
                }
            },

        },
        "size": 0,
    }


from EDR.servers.Elasticsearch import ElasticsearchAPI
def Output___Process_Behavior_Aggregation(ProcessCycleId:int, es: ElasticsearchAPI, INDEX_PATTERN:str)->list[dict]:
    output = []
    
    # 네트워크
    output.append(
        {
            "network": es.Query(
                            query=Network__aggregation_query____(ProcessCycleId),
                            index=INDEX_PATTERN,
                            is_aggs=True
                        )["network_event_aggregation"]["buckets"]
        }
        
    )
    
    # 레지스트리
    output.append(
        {
            "registry":es.Query(
                            query=Registry__aggregation_query____(ProcessCycleId),
                            index=INDEX_PATTERN,
                            is_aggs=True
                        )["registry_event_aggregation"]["buckets"]
        }
    )
    
    # 파일시스템
    output.append(
        {
            "filesystem":es.Query(
                            query=FileSystem__aggregation_query____(ProcessCycleId),
                            index=INDEX_PATTERN,
                            is_aggs=True
                        )["file_system_event_aggregation"]["buckets"]
        }
    )
    
    return output
        







