# NDR ElasticSearch 인덱스 정의

Common_component_template_name = "common_component"
Common_component_template = {
    "template": {
        "settings": {
            "number_of_shards":   1,
            "number_of_replicas": 1,
        },
        "mappings": {
            "common": { 
					"properties": {
						"Local_Ip": {  # NDR 탐지된 Network 인터페이스 IP
							"type": "ip",
						},
						"Mac_Address": { # NDR 탐지된 Network 인터페이스 IP의 MAC
							"type": "keyword",
						},
						"Timestamp": {
							"type": "date",
						},
					},
				},
        },
        "aliases": {
			"common_index": {},
		},
	},
	"_meta": {
		"description": "common 유형의 컴포넌트, 이 기종 간 호환되는 로그 필드",
		"version":     1,
	},
}


NDR_categorical_component_template_name = "ndr_categorical_component"
NDR_categorical_component_template = {
    "template": {
        "settings": {
            "number_of_shards":   1,
            "number_of_replicas": 1,
        },
        "mappings": {
            "common": { 
					"properties": {
						"Host_Ip": { # host ip 
							"type": "ip",
						},
						"Host_Mac_Address": { # host ip mac 
							"type": "keyword",
						},
					},
				},
        },
        "aliases": {
			"categorical_index": {},
		},
	},
	"_meta": {
		"description": "categorical 유형의 컴포넌트, NDR 간 호환되는 로그 필드",
		"version":     1,
	},
}


## NDR index template

index_patterns = "siem-ndr-*"
index_name = "siem-ndr-server"
template_name = "siem-ndr-server-index-template"
template = {

    "index_patterns": index_patterns,

    "priority":       298,
    "composed_of": [
        Common_component_template_name,
        NDR_categorical_component_template_name
    ],
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
                "unique": {
                    "properties": {
                        "suricata": {
                            "properties": {}
                        },
                        "mitmproxy": {
                            "properties": {}
                        }
                    }
                }
            }
        }
    }
}


