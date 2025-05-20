package siem

import (
	"fmt"

	elasticsearch_ "CoreServer/SIEM/elasticsearch"
	"CoreServer/util"

	"github.com/elastic/go-elasticsearch/v8"
)

type ElasticSearchManager struct {
	ElasticSearch_Object *elasticsearch_.ElasticSearch
}

func New_ElasticSearchManager(
	ServerIP string,
	Port int,
) *ElasticSearchManager {

	config := elasticsearch.Config{
		Addresses: []string{fmt.Sprintf("http://%s:%d", ServerIP, Port)},
	}

	/* 초기화 작업 */
	// 템플릿 생성

	// 인덱스 생성

	object := &ElasticSearchManager{
		ElasticSearch_Object: elasticsearch_.New_ElasticSearch(config),
	}

	// 초기화 작업
	// common 컴포넌트
	object.Create_component_template(
		Common_component_template_name,
		util.ERROR_PROCESSING(util.Map_to_JSON(Common_component)),
	)
	// categorical 컴포넌트
	object.Create_component_template(
		EDR_categorical_component_template_name,
		util.ERROR_PROCESSING(util.Map_to_JSON(EDR_categorical_component)),
	)
	// 프로세스 행위 템플릿
	object.Create_template(
		Edr_process_behavior_event_template_name,
		util.ERROR_PROCESSING(util.Map_to_JSON(Edr_process_behavior_event_template)),
	)

	return object

}

// 인덱스 생성, 이미 인덱스가 있으면 false
func (esM *ElasticSearchManager) Create_index(index string) (bool, error) {
	return esM.ElasticSearch_Object.Create_index(index)
}

// 템플릿 생성, 이미 템플릿이 있으면 false
// 각 솔루션마다 별도의 템플릿이 있을 때 사용한다
func (esM *ElasticSearchManager) Create_template(index_name string, json_template string) (bool, error) {
	return esM.ElasticSearch_Object.Create_template(index_name, json_template)
}

func (esM *ElasticSearchManager) Create_component_template(template_name string, json_template string) (bool, error) {
	return esM.ElasticSearch_Object.Create_component_template(template_name, json_template)
}

// 이미 존재하는 인덱스에 문서 추가 ( 사용 금지 )
//func (esM *ElasticSearchManager) AddDocument(index_name string, json_template string) (bool, error) {
//	return esM.ElasticSearch_Object.AddDocument(index_name, json_template)
//}

/*
// Get IP 정보
func (esM *ElasticSearchManager) Get_IP_info(ip string) (map[string]interface{}, error) {
	return esM.ElasticSearch_Object.Get_IP_info(ip)
}
*/

// 아래는 코어서버가 엘라스틱서치에 전달하는 데이터

/* 여분 엘라스틱서치 전용 타입을 위한 구조 */
type ElasticSearch_geo_point struct {
	Lat float64
	Lon float64
}

// ---

/* 지원 함수 개발 */
type Common_Event struct {
	Local_IP    string // 로컬 IP
	Mac_Address string // MAC 주소
	Timestamp   string // 당시 시간
}

type Categorical_Event struct {
	Agent_Id                          string // 에이전트 ID
	Process_Life_Cycle_Id             string // 프로세스 생애주기 ID
	Parent_Process_Life_Cycle_Id      string // 직계 부모 프로세스 생애주기 ID
	Root_Parent_Process_Life_Cycle_Id string // 최상위 부모(최초조상) 프로세스 생애주기 ID
	Root_Is_running_by_user           bool   // 최상위 부모(최초조상) 프로세스가 "유저의 의해" 실행했는 지 여부
	OS_info                           string // OS 정보
}

// Unique -> 행위 -> 프로세스 생성 이벤트 구조
type Unique_Behavior_Process_Created_Event struct {
	ProcessId     string
	ProcessSHA256 string
	ImagePath     string
	ImageSize     uint32
	CommandLine   string

	Parent_ProcessSHA256 string
	Parent_ImagePath     string
	Parent_ImageSize     uint32
}
type Unique_Behavior_Child_Process_Created_Event struct {
	Child_ProcessId     string
	Child_ProcessSHA256 string
	Child_ImagePath     string
	Child_ImageName     string
	Child_ImageSize     uint32
	Child_CommandLine   string
	//Child_Process_Life_Cycle_Id string
}

// Unique -> 행위 -> 파일 시스템 이벤트 구조
type Unique_Behavior_file_system_Event struct {
	FilePath   string
	Size       uint32
	FileSha256 string
	Action     string
}

// Unique -> 행위 -> 네트워크 이벤트 구조
type Unique_Behavior_network_Event struct {
	Remote_IP   string
	Remote_Port uint32
	Protocol    string
	Direction   string
	PacketSize  uint32
	Geoip       Unique_Geoip_Event
}

// Unique -> 행위 -> 레지스트리 이벤트 구조
type Unique_Behavior_registry_Event struct {
	RegistryObjectName string
	RegistryKey        string
}

// Unique -> 행위 -> 프로세스 종료 이벤트 구조
type Unique_Behavior_Process_Terminated_Event struct {
	Timestamp string
}

// Unique -> 행위 -> 이미지 로드 이벤트 구조
type Unique_Behavior_image_load_Event struct {
	ImageFullPath string
	SHA256        string
	Size          uint32
}

// GEO world map을 위한 자체 구조
type Unique_Geoip_Event struct {
	Ip         string
	Country    string
	Region     string
	RegionName string
	TimeZone   string
	City       string
	Zip        string
	Isp        string
	Org        string
	As         string
	Location   ElasticSearch_geo_point
}

// 함수

// / 로그 묶음
func Get_categorical_event(
	AGENT_ID string, OS_info string,
	Process_Life_Cycle_ID string, Parent_Process_Life_Cycle_Id string, Root_Parent_Process_Life_Cycle_Id string, Root_is_running_by_user bool,
) map[string]interface{} {
	return map[string]interface{}{
		"Agent_Id":     AGENT_ID,
		"OS_info":      OS_info,
		"Agent_status": true, // 에이전트 연결 상태
		"process_info": get_process_info_in_unique(Process_Life_Cycle_ID, Parent_Process_Life_Cycle_Id, Root_Parent_Process_Life_Cycle_Id, Root_is_running_by_user),
	}
}

func Get_common_event(Local_IP string, Mac_Address string, Timestamp string) map[string]interface{} {
	return map[string]interface{}{
		"Local_IP":    Local_IP,
		"Mac_Address": Mac_Address,
		"Timestamp":   Timestamp,
	}
}

func get_process_info_in_unique(Process_Life_Cycle_ID string, Parent_Process_Life_Cycle_Id string, Root_Parent_Process_Life_Cycle_Id string, Root_is_running_by_user bool) map[string]interface{} {
	return map[string]interface{}{
		"Process_Life_Cycle_Id":             Process_Life_Cycle_ID,
		"Parent_Process_Life_Cycle_Id":      Parent_Process_Life_Cycle_Id,
		"Root_Parent_Process_Life_Cycle_Id": Root_Parent_Process_Life_Cycle_Id,
		"Root_is_running_by_user":           Root_is_running_by_user,
	}
}

//
// index template
//

// 1. common 컴포넌트
var Common_component_template_name = "common_component" // 소문자로 하라
var Common_component = map[string]interface{}{
	"template": map[string]interface{}{
		"settings": map[string]interface{}{
			"number_of_shards":   1,
			"number_of_replicas": 1,
		},
		"mappings": map[string]interface{}{
			"properties": map[string]interface{}{
				"common": map[string]interface{}{ // 이기종 간 공통 정보 (엔드포인트, 네트워크 장비 모두 공통)
					"properties": map[string]interface{}{
						"Local_Ip": map[string]interface{}{ // 로컬 IP
							"type": "ip",
						},
						"Mac_Address": map[string]interface{}{ // MAC 주소
							"type": "keyword",
						},
						"Timestamp": map[string]interface{}{ // 당시 시간
							"type": "date",
						},
					},
				},
			},
		},
		"aliases": map[string]interface{}{
			"common_index": map[string]interface{}{},
		},
	},
	"_meta": map[string]interface{}{
		"description": "common 유형의 컴포넌트, 이기종 간 호환되는 로그 필드",
		"version":     1,
	},
}

// 2. categorical 컴포넌트
var EDR_categorical_component_template_name = "edr_categorical_component" // 소문자로 하라
var EDR_categorical_component = map[string]interface{}{
	"template": map[string]interface{}{
		"settings": map[string]interface{}{
			"number_of_shards":   4,
			"number_of_replicas": 1,
		},
		"mappings": map[string]interface{}{
			"properties": map[string]interface{}{
				"categorical": map[string]interface{}{ // 특정 기종간 정보 ( 엔드포인트, 네트워크 장비 등등 특정 영역끼리 공유 )
					"properties": map[string]interface{}{
						"Agent_Id": map[string]interface{}{ // 에이전트 ID
							"type": "keyword",
						},
						"OS_info": map[string]interface{}{ // OS 정보
							"type": "text", // 주로 OS 및 버전 정보가 들어가므로 text.
						},
						"Agent_status": map[string]interface{}{ // 에이전트 상태
							"type": "boolean",
						},
						"process_info": map[string]interface{}{ // 프로세스 정보
							"properties": map[string]interface{}{
								// 아래는 나중에 프로세스간 연관분석시에 활용
								"Process_Life_Cycle_Id": map[string]interface{}{ // 프로세스 생애주기 ID
									"type": "keyword",
								},
								"Parent_Process_Life_Cycle_Id": map[string]interface{}{ // 직계 부모 프로세스 생애주기 ID
									"type": "keyword",
								},
								"Root_Parent_Process_Life_Cycle_Id": map[string]interface{}{ // 최상위 부모(최초조상) 프로세스 생애주기 ID
									"type": "keyword",
								},
								"Root_is_running_by_user": map[string]interface{}{ // 최상위 부모(최초조상) 프로세스가 "유저의 의해" 실행했는 지 여부
									"type": "boolean",
								},
							},
						},
					},
				},
			},
		},
		"aliases": map[string]interface{}{
			"categorical_index": map[string]interface{}{},
		},
	},
	"_meta": map[string]interface{}{
		"description": "categorical 유형의 컴포넌트, EDR 간 호환되는 로그 필드",
		"version":     1,
	},
}

// 3. EDR 프로세스 행위기반 전용 index 템플릿
var Edr_process_behavior_event_template_name = "siem-edr-processbehavior-event-template"
var Edr_process_behavior_event_template = map[string]interface{}{
	"index_patterns": []string{"siem-edr-processbehavior-event*"},
	"composed_of": []string{
		Common_component_template_name,
		EDR_categorical_component_template_name,
	},
	"priority": 500,
	"template": map[string]interface{}{
		"settings": map[string]interface{}{
			"number_of_shards":   1,
			"number_of_replicas": 1,
		},
		"mappings": map[string]interface{}{
			"properties": map[string]interface{}{
				"unique": map[string]interface{}{ // 고유 정보 ( 엔드포인트 기종 중에서, 각자의 고유 정보 (솔루션 A만의 로깅 정보를 예시로 들 수 있다.) )
					"properties": map[string]interface{}{
						"process_behavior_events": map[string]interface{}{
							"properties": map[string]interface{}{
								//
								"Process_Created": map[string]interface{}{ // 1. 프로세스 생성 이벤트
									"properties": map[string]interface{}{
										"ProcessId": map[string]interface{}{ // 생성한 프로세스 ID
											"type": "keyword",
										},
										"ProcessSHA256": map[string]interface{}{ // 생성한 프로세스 SHA256
											"type": "keyword",
										},
										"ImagePath": map[string]interface{}{ // 생성한 프로세스 이미지 경로
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"ImageSize": map[string]interface{}{ // 생성한 프로세스 이미지 크기
											"type": "long",
										},
										"CommandLine": map[string]interface{}{ // 생성한 프로세스 명령줄
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"Parent_ProcessSHA256": map[string]interface{}{ // 생성한 프로세스 SHA256
											"type": "keyword",
										},
										"Parent_ImagePath": map[string]interface{}{ // 생성한 프로세스 이미지 경로
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"Parent_ImageSize": map[string]interface{}{ // 생성한 프로세스 이미지 크기
											"type": "long",
										},
									},
								},
								"Child_Process_Created": map[string]interface{}{ // 자식 프로세스 생성 이벤트
									"properties": map[string]interface{}{
										"Child_ProcessId": map[string]interface{}{ // 생성한 프로세스 ID
											"type": "keyword",
										},
										"Child_ProcessSHA256": map[string]interface{}{ // 생성한 자식 프로세스 SHA256
											"type": "keyword",
										},
										"Child_ImagePath": map[string]interface{}{ // 생성한 자식 프로세스 이미지 경로
											"type": "keyword",
										},
										"Child_ImageSize": map[string]interface{}{ // 생성한 자식 프로세스 이미지 크기
											"type": "long",
										},
										"Child_CommandLine": map[string]interface{}{ // 생성한 자식 프로세스 명령줄
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"Child_Process_Life_Cycle_Id": map[string]interface{}{ // 프로세스 생애주기 ID
											"type": "keyword",
										},
									},
								},
								"file_system": map[string]interface{}{ // 2. 파일 시스템 이벤트
									"properties": map[string]interface{}{
										"FilePath": map[string]interface{}{ // 파일 경로
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"FileSize": map[string]interface{}{ // 파일 크기
											"type": "long",
										},
										"Action": map[string]interface{}{ // 생성/삭제/이름변경 등 여부
											"type": "keyword",
										},
									},
								},
								"network": map[string]interface{}{ // 3. 네트워크 이벤트
									"properties": map[string]interface{}{
										"RemoteIp": map[string]interface{}{ // 원격 IP
											"type": "ip",
										},
										"RemotePort": map[string]interface{}{ // 원격 포트
											"type": "integer",
										},
										"Protocol": map[string]interface{}{ // 프로토콜
											"type": "keyword",
										},
										"Direction": map[string]interface{}{ // 수신/송신
											"type": "keyword",
										},
										"PacketSize": map[string]interface{}{ // 패킷 크기
											"type": "long",
										},
										// [+] IP 조회 정보 추가
										"geoip": map[string]interface{}{
											"properties": map[string]interface{}{
												"Ip": map[string]interface{}{ // IP 정보
													"type": "ip",
												},

												"Country": map[string]interface{}{ // 국가 정보
													"type": "keyword",
												},
												"Region": map[string]interface{}{
													"type": "keyword",
												},
												"RegionName": map[string]interface{}{
													"type": "keyword",
												},

												"TimeZone": map[string]interface{}{ // 시간대 정보
													"type": "keyword",
												},

												"City": map[string]interface{}{ // 도시 정보
													"type": "keyword",
												},
												"Zip": map[string]interface{}{ // 우편번호 정보
													"type": "keyword",
												},
												"Isp": map[string]interface{}{ // ISP 정보
													"type": "keyword",
												},
												"Org": map[string]interface{}{ // 조직 정보
													"type": "keyword",
												},
												"As": map[string]interface{}{ // AS 정보
													"type": "text",
													"fields": map[string]interface{}{ // .keyword 필드 추가
														"keyword": map[string]interface{}{
															"type":         "keyword",
															"ignore_above": 512, // 필요에 따라 길이 제한 설정
														},
													},
												},
												"location": map[string]interface{}{ // 위치 정보
													"type": "geo_point",

													/*
														{
															"lat": 33.44,
															"lon": -112.22 이런 형식
														}
													*/
												},
											},
										},
									},
								},
								"registry": map[string]interface{}{ // 4. 레지스트리 이벤트
									"properties": map[string]interface{}{
										"RegistryKey": map[string]interface{}{ // 레지스트리 함수
											"type": "keyword",
										},
										"RegistryObjectName": map[string]interface{}{ // 레지스트리 객체 이름
											"type": "keyword",
										},

										"RegistryValueName": map[string]interface{}{ // 레지스트리 값 이름
											"type": "text",
											"fields": map[string]interface{}{ // .keyword 필드 추가
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512, // 필요에 따라 길이 제한 설정
												},
											},
										},
										"RegistryValueType": map[string]interface{}{ // 레지스트리 값 타입
											"type": "keyword",
										},

										"RegistryValueData": map[string]interface{}{ // 레지스트리 값 데이터
											"type": "keyword",
										},
									},
								},
								"image_load": map[string]interface{}{ // 5. 이미지 로드 이벤트
									"properties": map[string]interface{}{
										"ImagePath": map[string]interface{}{ // 이미지 경로
											"type": "keyword",
										},
										"ImageSHA256": map[string]interface{}{ // 이미지 SHA256
											"type": "keyword",
										},
										"ImageSize": map[string]interface{}{ // 이미지 크기
											"type": "long",
										},
									},
								},
								"Process_Terminated": map[string]interface{}{ // 5. 프로세스 종료 이벤트
									"properties": map[string]interface{}{
										"Timestamp": map[string]interface{}{ // 당시 시간
											"type": "date",
										},
									},
								},
								//
							},
						},
						"LLM": map[string]interface{}{ // 6. LLM 분석결과
							"properties": map[string]interface{}{
								"TYPE_EVAL": map[string]interface{}{ // 유형평가

									"properties": map[string]interface{}{

										"behavior": map[string]interface{}{ // 유형 행동 (network, filesystem 등)
											"type": "keyword",
										},
										"events": map[string]interface{}{ // 이벤트 목록
											"properties": map[string]interface{}{

												"summary": map[string]interface{}{ // 유형 요약
													"type": "text",
													"fields": map[string]interface{}{
														"keyword": map[string]interface{}{
															"type":         "keyword",
															"ignore_above": 512,
														},
													},
												},
												"detail_report": map[string]interface{}{ // 상세 리포트
													"type": "text",
													"fields": map[string]interface{}{
														"keyword": map[string]interface{}{
															"type":         "keyword",
															"ignore_above": 512,
														},
													},
												},
												"tags": map[string]interface{}{ // 태그
													"type": "keyword",
												},
												"report_with_timeline": map[string]interface{}{ // 타임스탬프 기반 이벤트 하이라이트
													"properties": map[string]interface{}{
														"timestamp": map[string]interface{}{ // 타임스탬프
															"type": "date",
														},
														"event": map[string]interface{}{ // 해당 타임스탬프에 발생한 이벤트 문장
															"type": "text",
															"fields": map[string]interface{}{
																"keyword": map[string]interface{}{
																	"type":         "keyword",
																	"ignore_above": 512,
																},
															},
														},
													},
												},
											},
										},
									},
								},
								"MIDDLE_EVAL": map[string]interface{}{ // 중간평가

									"properties": map[string]interface{}{
										"ALL_behaviors_relative_report_by_Timestamp": map[string]interface{}{ // 중간 요약
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
										"ALL_behaviors_flow_report_by_Timestamp": map[string]interface{}{ // flow흐름 -> mermaid로 나타낼 것이므로 index 템플릿에 필요없음
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
										"report": map[string]interface{}{ // 중간 리포트
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
										"tags": map[string]interface{}{ // 태그
											"type": "keyword",
										},
										"pattern": map[string]interface{}{ // 탐지한 패턴
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
									},
								},
								"FINAL_EVAL": map[string]interface{}{ // 최종평가
									"properties": map[string]interface{}{
										"ALL_Processes_Timeline": map[string]interface{}{ // 프로세스 간 전체 타임라인
											"properties": map[string]interface{}{
												"timestamp": map[string]interface{}{ // 타임스탬프
													"type": "date",
												},
												"event": map[string]interface{}{ // 해당 타임스탬프에 발생한 이벤트 문장
													"type": "text",
													"fields": map[string]interface{}{
														"keyword": map[string]interface{}{
															"type":         "keyword",
															"ignore_above": 512,
														},
													},
												},
												"Process_Life_Cycle_Id": map[string]interface{}{ // 프로세스 생애주기 ID
													"type": "keyword",
												},
											},
										},
										"Warning_Process": map[string]interface{}{ // 프로세스 Tree내 위험한 프로세스 확인
											"properties": map[string]interface{}{
												"Process_Life_Cycle_Id": map[string]interface{}{ // 프로세스 생애주기 ID
													"type": "keyword",
												},
												"reason": map[string]interface{}{ // 이유
													"type": "text",
													"fields": map[string]interface{}{
														"keyword": map[string]interface{}{
															"type":         "keyword",
															"ignore_above": 512,
														},
													},
												},
											},
										},
										"pattern": map[string]interface{}{ // 탐지한 패턴
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
										"anomaly_score": map[string]interface{}{ // 변칙 점수
											"type": "float",
										},
										"severity": map[string]interface{}{ // 심각도
											"type": "keyword",
										},
										"severity_reason": map[string]interface{}{ // 심각도 이유
											"type": "text",
											"fields": map[string]interface{}{
												"keyword": map[string]interface{}{
													"type":         "keyword",
													"ignore_above": 512,
												},
											},
										},
									},
								},
							},
						},
						/* 모든 솔루션이 제공해야하는 Response 공통 필드로, SIEM/SOAR에서 이 정보를 참조한다. */
						"response_info": map[string]interface{}{
							"properties": map[string]interface{}{
								"restapi_server_ip": map[string]interface{}{
									"type": "ip",
								},
								"restapi_server_port": map[string]interface{}{
									"type": "integer",
								},
								"apis": map[string]interface{}{ // 차단가능한 API 목록
									"type": "nested",
									"properties": map[string]interface{}{
										"sub_dir": map[string]interface{}{ // /API/v1.. 이런 거
											"type": "keyword",
										},
										"method": map[string]interface{}{ // GET, POST 등
											"type": "keyword",
										},
										"parameters": map[string]interface{}{ // parameters Array
											"type": "nested",
											"properties": map[string]interface{}{
												"arg_name": map[string]interface{}{ // 파라미터 이름
													"type": "keyword",
												},
												"arg_type": map[string]interface{}{ // 파라미터 타입 (json, string 등)
													"type": "keyword",
												},
											},
										},
									},
								},
							},
						},
					},
				},
			},
		},
	},
}
