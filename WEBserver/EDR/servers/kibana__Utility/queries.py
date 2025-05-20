# ALL_DASHBOARD
## 총 이벤트량 - ALL_EVENTS_Pie_Chart
ALL_EVENTS_Pie_Chart = ALL_EVENTS ={
      "aggs": {
        "0": {
          "filters": {
            "filters": {
              "네트워크": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.network"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "파일 시스템": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.file_system"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "레지스트리": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.registry"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "프로세스 종료": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Terminated"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "프로세스 생성": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Created"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "이미지 로드": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.image_load"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              }
            }
          },
          "aggs": {
            "1": {
              "terms": {
                "field": "categorical.Agent_Id",
                "order": {
                  "_count": "desc"
                },
                "size": 3,
                "shard_size": 25
              },
              "aggs": {
                "2": {
                  "terms": {
                    "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
                    "order": {
                      "_count": "desc"
                    },
                    "size": 3,
                    "shard_size": 25
                  }
                }
              }
            }
          }
        }
      },
      "size": 0,
      "_source": {
        "excludes": []
      },
      "query": {
        "bool": {
          "must": [],
          "filter": [], # 시간 범위 적용은 kibanaDashboard 클래스에서 처리해야 함
          "should": [],
          "must_not": []
        }
      },
      "stored_fields": [
        "*"
      ],
      "runtime_mappings": {},
      "script_fields": {},
      "fields": [
        {
          "field": "@timestamp",
          "format": "date_time"
        },
        {
          "field": "common.Timestamp",
          "format": "date_time"
        },
        {
          "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
          "format": "date_time"
        },
        {
          "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
          "format": "date_time"
        },
        {
          "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
          "format": "date_time"
        }
      ]
    }




## 전체 이벤트 발생 이벤트
ALL_EVENTS_Area_Chart = {
  "aggs": {
    "0": {
      "date_histogram": {
        "field": "common.Timestamp",
        "fixed_interval": "12h",
        "time_zone": "Asia/Seoul",
        "extended_bounds": {
          "min": 1744375948571,
          "max": 1745412748571
        }
      },
      "aggs": {
        "1": {
          "filters": {
            "filters": {
              "파일 시스템": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.file_system"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "프로세스 생성": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Created"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "레지스트리": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.registry"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "이미지 로드": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.image_load"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "네트워크": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.network"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              },
              "프로세스 종료": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Terminated"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              }
            }
          },
          "aggs": {
            "2-bucket": {
              "filter": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              }
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
# -> 행동
IMAGELOAD_BEHAVIOR_TimeLine_EVENTS = {
  "aggs": {
    "0": {
      "date_histogram": {
        "field": "common.Timestamp",
        "fixed_interval": "30m",
        "time_zone": "UTC",
        "extended_bounds": {
          "min": 1745551394194,
          "max": 1745637794194
        }
      },
      "aggs": {
        "1-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "exists": {
                          "field": "unique.process_behavior_events.image_load.ImagePath"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

IMAGELOAD_BEHAVIOR_recently_EVENTS = {
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "4": "desc"
        },
        "size": 3,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "terms": {
            "field": "categorical.process_info.Process_Life_Cycle_Id",
            "order": {
              "4": "desc"
            },
            "size": 3,
            "shard_size": 25
          },
          "aggs": {
            "2": {
              "terms": {
                "field": "unique.process_behavior_events.image_load.ImageSHA256",
                "order": {
                  "4": "desc"
                },
                "size": 3,
                "shard_size": 25
              },
              "aggs": {
                "3": {
                  "terms": {
                    "field": "unique.process_behavior_events.image_load.ImagePath",
                    "order": {
                      "4": "desc"
                    },
                    "size": 3,
                    "shard_size": 25
                  },
                  "aggs": {
                    "4": {
                      "min": {
                        "field": "common.Timestamp"
                      }
                    }
                  }
                },
                "4": {
                  "min": {
                    "field": "common.Timestamp"
                  }
                }
              }
            },
            "4": {
              "min": {
                "field": "common.Timestamp"
              }
            }
          }
        },
        "4": {
          "min": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [

      ],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

IMAGELOAD_BEHAVIOR_cloud_tags_EVENTS = { # 사용안함
  "aggs": {
    "0": {
      "terms": {
        "field": "unique.process_behavior_events.image_load.ImagePath",
        "order": {
          "_count": "desc"
        },
        "size": 10
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}


NETWORK_BEHAVIOR_remoteip_packet_count_BAR_EVENTS ={
  "aggs": {
    "0": {
      "terms": {
        "field": "unique.process_behavior_events.network.RemoteIp",
        "order": {
          "1-bucket": "desc"
        },
        "size": 6,
        "shard_size": 25
      },
      "aggs": {
        "1-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "UDP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "2-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "TCP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "3-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "ICMP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "4-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "UDP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      },
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "TCP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      },
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "ICMP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
NETWORK_BEHAVIOR_remoteip_recently_remoteip_EVENTS = {
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "7": "desc"
        },
        "size": 5,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "terms": {
            "field": "categorical.process_info.Process_Life_Cycle_Id",
            "order": {
              "7": "desc"
            },
            "size": 3,
            "shard_size": 25
          },
          "aggs": {
            "2": {
              "terms": {
                "field": "unique.process_behavior_events.network.RemoteIp",
                "order": {
                  "7": "desc"
                },
                "size": 5,
                "shard_size": 25
              },
              "aggs": {
                "3": {
                  "terms": {
                    "field": "unique.process_behavior_events.network.RemotePort",
                    "order": {
                      "7": "desc"
                    },
                    "size": 5,
                    "shard_size": 25
                  },
                  "aggs": {
                    "4": {
                      "terms": {
                        "field": "unique.process_behavior_events.network.Protocol",
                        "order": {
                          "7": "desc"
                        },
                        "size": 5,
                        "shard_size": 25
                      },
                      "aggs": {
                        "5": {
                          "terms": {
                            "field": "unique.process_behavior_events.network.geoip.Country",
                            "order": {
                              "7": "desc"
                            },
                            "size": 3,
                            "shard_size": 25
                          },
                          "aggs": {
                            "6": {
                              "terms": {
                                "field": "unique.process_behavior_events.network.geoip.Org",
                                "order": {
                                  "7": "desc"
                                },
                                "size": 3,
                                "shard_size": 25
                              },
                              "aggs": {
                                "7": {
                                  "min": {
                                    "field": "common.Timestamp"
                                  }
                                }
                              }
                            },
                            "7": {
                              "min": {
                                "field": "common.Timestamp"
                              }
                            }
                          }
                        },
                        "7": {
                          "min": {
                            "field": "common.Timestamp"
                          }
                        }
                      }
                    },
                    "7": {
                      "min": {
                        "field": "common.Timestamp"
                      }
                    }
                  }
                },
                "7": {
                  "min": {
                    "field": "common.Timestamp"
                  }
                }
              }
            },
            "7": {
              "min": {
                "field": "common.Timestamp"
              }
            }
          }
        },
        "7": {
          "min": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [
        {
          "match_phrase": {
              "categorical.process_info.Process_Life_Cycle_Id": "프로세스 ID 식별 값"
          }
        },

        {
            "range": {
                "common.Timestamp": {
                    "format": "strict_date_optional_time",
                    "gte": "최대 타임스탬프 값", # 최대
                    "lte": "최소 타임스탬프 값", # 최저
                }
            }
        }

      ],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
REGISTRY_BEHAVIOR_timeline_count_EVENTS ={
  "aggs": {
    "0": {
      "terms": {
        "field": "unique.process_behavior_events.network.RemoteIp",
        "order": {
          "1-bucket": "desc"
        },
        "size": 6,
        "shard_size": 25
      },
      "aggs": {
        "1-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "UDP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "2-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "TCP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "3-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.network.Protocol": {
                            "value": "ICMP"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        },
        "4-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "UDP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      },
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "TCP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      },
                      {
                        "bool": {
                          "should": [
                            {
                              "match_phrase": {
                                "! unique.process_behavior_events.network.Protocol": "ICMP"
                              }
                            }
                          ],
                          "minimum_should_match": 1
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
REGISTRY_BEHAVIOR_timeline_recently_EVENTS={
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "5": "desc"
        },
        "size": 3,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "terms": {
            "field": "categorical.process_info.Process_Life_Cycle_Id",
            "order": {
              "5": "desc"
            },
            "size": 3,
            "shard_size": 25
          },
          "aggs": {
            "2": {
              "filters": {
                "filters": {
                  "unique.process_behavior_events.registry:*": {
                    "bool": {
                      "must": [],
                      "filter": [
                        {
                          "bool": {
                            "should": [
                              {
                                "exists": {
                                  "field": "unique.process_behavior_events.registry"
                                }
                              }
                            ],
                            "minimum_should_match": 1
                          }
                        }
                      ],
                      "should": [],
                      "must_not": []
                    }
                  }
                }
              },
              "aggs": {
                "3": {
                  "terms": {
                    "field": "unique.process_behavior_events.registry.RegistryKey",
                    "order": {
                      "5": "desc"
                    },
                    "size": 3,
                    "shard_size": 25
                  },
                  "aggs": {
                    "4": {
                      "terms": {
                        "field": "unique.process_behavior_events.registry.RegistryObjectName",
                        "order": {
                          "5": "desc"
                        },
                        "size": 1,
                        "shard_size": 25
                      },
                      "aggs": {
                        "5": {
                          "min": {
                            "field": "common.Timestamp"
                          }
                        }
                      }
                    },
                    "5": {
                      "min": {
                        "field": "common.Timestamp"
                      }
                    }
                  }
                }
              }
            },
            "5": {
              "min": {
                "field": "common.Timestamp"
              }
            }
          }
        },
        "5": {
          "min": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
REGISTRY_BEHAVIOR_registry_key_frequency_EVENTS = {
  "aggs": {
    "0": {
      "terms": {
        "field": "unique.process_behavior_events.registry.RegistryKey",
        "order": {
          "_count": "desc"
        },
        "size": 5,
        "shard_size": 25
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

FILESYSTEM_BEHAVIOR_timeline_count_EVENTS ={
  "aggs": {
    "0": {
      "filters": {
        "filters": {
          "Create": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.file_system.Action": {
                            "value": "Create"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "Read": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.file_system.Action": {
                            "value": "Read"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "Delete": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.file_system.Action": {
                            "value": "Delete"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          },
          "Write": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "term": {
                          "unique.process_behavior_events.file_system.Action": {
                            "value": "Write"
                          }
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

FILESYSTEM_BEHAVIOR_timeline_recently_EVENTS={
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "4": "desc"
        },
        "size": 5,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "terms": {
            "field": "categorical.process_info.Process_Life_Cycle_Id",
            "order": {
              "4": "desc"
            },
            "size": 3,
            "shard_size": 25
          },
          "aggs": {
            "2": {
              "terms": {
                "field": "unique.process_behavior_events.file_system.Action",
                "order": {
                  "4": "desc"
                },
                "size": 3,
                "shard_size": 25
              },
              "aggs": {
                "3": {
                  "terms": {
                    "field": "unique.process_behavior_events.file_system.FilePath.keyword",
                    "order": {
                      "4": "desc"
                    },
                    "size": 1000
                  },
                  "aggs": {
                    "4": {
                      "max": {
                        "field": "common.Timestamp"
                      }
                    }
                  }
                },
                "4": {
                  "max": {
                    "field": "common.Timestamp"
                  }
                }
              }
            },
            "4": {
              "max": {
                "field": "common.Timestamp"
              }
            }
          }
        },
        "4": {
          "max": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

PROCESS_BEHAVIOR_Created_EVENTS ={
  "aggs": {
    "0": {
      "date_histogram": {
        "field": "common.Timestamp",
        "fixed_interval": "30m",
        "time_zone": "UTC",
        "extended_bounds": {
          "min": 1745603641859,
          "max": 1745690041859
        }
      },
      "aggs": {
        "1-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "exists": {
                          "field": "unique.process_behavior_events.Process_Created"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}



PROCESS_BEHAVIOR_Terminated_EVENTS ={
  "aggs": {
    "0": {
      "date_histogram": {
        "field": "common.Timestamp",
        "fixed_interval": "30m",
        "time_zone": "UTC",
        "extended_bounds": {
          "min": 1745603767841,
          "max": 1745690167841
        }
      },
      "aggs": {
        "1-bucket": {
          "filter": {
            "bool": {
              "must": [],
              "filter": [
                {
                  "bool": {
                    "should": [
                      {
                        "exists": {
                          "field": "unique.process_behavior_events.Process_Terminated"
                        }
                      }
                    ],
                    "minimum_should_match": 1
                  }
                }
              ],
              "should": [],
              "must_not": []
            }
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}


PROCESS_BEHAVIOR_Created_recently_EVENTS ={
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "5": "desc"
        },
        "size": 5,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "filters": {
            "filters": {
              "unique.process_behavior_events.Process_Created:*": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Created"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              }
            }
          },
          "aggs": {
            "2": {
              "terms": {
                "field": "categorical.process_info.Process_Life_Cycle_Id",
                "order": {
                  "5": "desc"
                },
                "size": 10,
                "shard_size": 25
              },
              "aggs": {
                "3": {
                  "terms": {
                    "field": "unique.process_behavior_events.Process_Created.ImagePath.keyword",
                    "order": {
                      "5": "desc"
                    },
                    "size": 100
                  },
                  "aggs": {
                    "4": {
                      "terms": {
                        "field": "unique.process_behavior_events.Process_Created.CommandLine.keyword",
                        "order": {
                          "5": "desc"
                        },
                        "size": 3,
                        "shard_size": 25
                      },
                      "aggs": {
                        "5": {
                          "min": {
                            "field": "common.Timestamp"
                          }
                        }
                      }
                    },
                    "5": {
                      "min": {
                        "field": "common.Timestamp"
                      }
                    }
                  }
                },
                "5": {
                  "min": {
                    "field": "common.Timestamp"
                  }
                }
              }
            }
          }
        },
        "5": {
          "min": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}

PROCESS_BEHAVIOR_Terminated_recently_EVENTS ={
  "aggs": {
    "0": {
      "terms": {
        "field": "categorical.process_info.Root_Parent_Process_Life_Cycle_Id",
        "order": {
          "3": "desc"
        },
        "size": 5,
        "shard_size": 25
      },
      "aggs": {
        "1": {
          "filters": {
            "filters": {
              "unique.process_behavior_events.Process_Terminated.Timestamp :*": {
                "bool": {
                  "must": [],
                  "filter": [
                    {
                      "bool": {
                        "should": [
                          {
                            "exists": {
                              "field": "unique.process_behavior_events.Process_Terminated.Timestamp"
                            }
                          }
                        ],
                        "minimum_should_match": 1
                      }
                    }
                  ],
                  "should": [],
                  "must_not": []
                }
              }
            }
          },
          "aggs": {
            "2": {
              "terms": {
                "field": "categorical.process_info.Process_Life_Cycle_Id",
                "order": {
                  "3": "desc"
                },
                "size": 100
              },
              "aggs": {
                "3": {
                  "max": {
                    "field": "common.Timestamp"
                  }
                }
              }
            }
          }
        },
        "3": {
          "max": {
            "field": "common.Timestamp"
          }
        }
      }
    }
  },
  "size": 0,
  "_source": {
    "excludes": []
  },
  "query": {
    "bool": {
      "must": [],
      "filter": [],
      "should": [],
      "must_not": []
    }
  },
  "stored_fields": [
    "*"
  ],
  "runtime_mappings": {},
  "script_fields": {},
  "fields": [
    {
      "field": "@timestamp",
      "format": "date_time"
    },
    {
      "field": "common.Timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_Processes_Timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.FINAL_EVAL.ALL_behaviors_flow_report_by_Timestamp.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.LLM.TYPE_EVAL.events.report_with_timeline.timestamp",
      "format": "date_time"
    },
    {
      "field": "unique.process_behavior_events.Process_Terminated.Timestamp",
      "format": "date_time"
    }
  ]
}
#

# 기존 쿼리에 agent_id 필터 추가
def Add_Agent_ID_filter(
        query:dict,
        agent_id:str
) -> dict:
    agent_filter = {
        "match_phrase": {
            "categorical.Agent_Id": agent_id
        }
    }

    query["query"]["bool"]["filter"].append(agent_filter)
    return query

# 기존 쿼리에 Root_Parent_Process_Life_Cycle_Id 필터 추가
def Add_Root_Parent_Process_Life_Cycle_Id_filter(
        query: dict,
        Root_Parent_Process_Life_Cycle_Id: str
) -> dict:
  agent_filter = {
    "match_phrase": {
      "categorical.process_info.Root_Parent_Process_Life_Cycle_Id": Root_Parent_Process_Life_Cycle_Id
    }
  }

  query["query"]["bool"]["filter"].append(agent_filter)
  return query

def Add_Process_Life_Cycle_id_filter(
        query: dict,
        Process_Life_Cycle_id: str
) -> dict:
    agent_filter = {
        "match_phrase": {
            "categorical.process_info.Process_Life_Cycle_Id": Process_Life_Cycle_id
        }
    }

    query["query"]["bool"]["filter"].append(agent_filter)
    return query

def Add_Query_String_filter(query:dict, query_string:str)->dict:
    query["query"]["bool"]["filter"].append(
        {
            "query_string": {
                "query": query_string
            }
        }
    )
    return query

from Utility.timestamper import Get_Current_Time, Set_Increase_Time, Set_Decrease_Time

# 타임스탬프 기준 범위 만들기 -> 이걸 해야 유효한 이벤트 범위를 만든다. AI에서도 조정을 하도록 해야함 None인 경우, 자동처리 1일간격씩 됨
def Set_time_filter( query:dict,increased_time:str, decreased_time:str)->dict:

    # 범위 적용

    query["query"]["bool"]["filter"].append(
        {
            "range": {
                "common.Timestamp": {
                    "format": "strict_date_optional_time",
                    "gte": decreased_time, # 최대
                    "lte": increased_time, # 최저
                }
            }
        }
    )

    print(query["query"]["bool"]["filter"])

    return query