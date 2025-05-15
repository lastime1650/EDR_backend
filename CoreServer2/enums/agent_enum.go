package enums

import "fmt"

type Agent_enum int32

const (
	// 커널 -> 분석서버 ( 1 xx xx )
	PsSetCreateProcessNotifyRoutine_Creation        Agent_enum = 10101 // 폐지됨
	PsSetCreateProcessNotifyRoutine_Remove          Agent_enum = 10102
	PsSetCreateProcessNotifyRoutine_Creation_Detail Agent_enum = 10103
	PsSetCreateThreadNotifyRoutine_Creation         Agent_enum = 10201 // 너무 로그가 많음 (보류)
	PsSetCreateThreadNotifyRoutine_Remove           Agent_enum = 10202 // 너무 로그가 많음 (보류)
	PsSetLoadImageNotifyRoutine_Load                Agent_enum = 10301
	CmRegisterCallbackEx                            Agent_enum = 10401
	Network_Traffic                                 Agent_enum = 10501
	File_System                                     Agent_enum = 10601

	// 차단
	Response_Process        Agent_enum = 10710
	Response_Process_Remove Agent_enum = 10711

	Response_Network        Agent_enum = 10720
	Response_Network_Remove Agent_enum = 10721

	Response_File        Agent_enum = 10730
	Response_File_Remove Agent_enum = 10731

	Get_Response_list Agent_enum = 10799

	// + API 후킹
	API_HOOKING Agent_enum = 10800 // API후킹전용

	// 분석서버 -> 커널 ( 2 xx xx )
	Request_ALL_Monitored_Data Agent_enum = 20101
	Request_Real_File          Agent_enum = 20201
	Running_Process_list       Agent_enum = 20301 // 현재 실행중인 프로세스 정보 모두 요청
	Request_PID_info           Agent_enum = 20401 // PID를 주면 그것에 대한 정보를 요청

	// 공통 확인
	SUCCESS Agent_enum = 90001
	FAIL    Agent_enum = 90002

	/* EDR 전용  enum */
	Agent_connect      Agent_enum = 90100 // 에이전트 연결돰
	Agent_lose_connect Agent_enum = 90101 // 에이전트 연결 해제 됨
)

// Agent_enum -> string
var AgentEnumNames = map[Agent_enum]string{
	PsSetCreateProcessNotifyRoutine_Creation:        "PsSetCreateProcessNotifyRoutine_Creation",
	PsSetCreateProcessNotifyRoutine_Remove:          "PsSetCreateProcessNotifyRoutine_Remove",
	PsSetCreateProcessNotifyRoutine_Creation_Detail: "PsSetCreateProcessNotifyRoutine_Creation_Detail",
	PsSetCreateThreadNotifyRoutine_Creation:         "PsSetCreateThreadNotifyRoutine_Creation",
	PsSetCreateThreadNotifyRoutine_Remove:           "PsSetCreateThreadNotifyRoutine_Remove",
	PsSetLoadImageNotifyRoutine_Load:                "PsSetLoadImageNotifyRoutine_Load",
	CmRegisterCallbackEx:                            "CmRegisterCallbackEx",
	Network_Traffic:                                 "Network_Traffic",
	File_System:                                     "File_System",
	Response_Process:                                "Response_Process",
	Response_Process_Remove:                         "Response_Process_Remove",
	Response_Network:                                "Response_Network",
	Response_Network_Remove:                         "Response_Network_Remove",
	Response_File:                                   "Response_File",
	Response_File_Remove:                            "Response_File_Remove",
	Get_Response_list:                               "Get_Response_list",
	API_HOOKING:                                     "API_HOOKING",
	Request_ALL_Monitored_Data:                      "Request_ALL_Monitored_Data",
	Request_Real_File:                               "Request_Real_File",
	Running_Process_list:                            "Running_Process_list",
	Request_PID_info:                                "Request_PID_info",
	SUCCESS:                                         "SUCCESS",
	FAIL:                                            "FAIL",
	Agent_connect:                                   "Agent_connect",
	Agent_lose_connect:                              "Agent_lose_connect",
}

func (a Agent_enum) String() (string, error) {
	if name, ok := AgentEnumNames[a]; ok {
		return name, nil
	}
	return "Unknown Agent_enum", fmt.Errorf("Unknown Agent_enum")
}

// string -> Agent_enum
var AgentEnumValues = map[string]Agent_enum{
	"PsSetCreateProcessNotifyRoutine_Creation":        PsSetCreateProcessNotifyRoutine_Creation,
	"PsSetCreateProcessNotifyRoutine_Remove":          PsSetCreateProcessNotifyRoutine_Remove,
	"PsSetCreateProcessNotifyRoutine_Creation_Detail": PsSetCreateProcessNotifyRoutine_Creation_Detail,
	"PsSetCreateThreadNotifyRoutine_Creation":         PsSetCreateThreadNotifyRoutine_Creation,
	"PsSetCreateThreadNotifyRoutine_Remove":           PsSetCreateThreadNotifyRoutine_Remove,
	"PsSetLoadImageNotifyRoutine_Load":                PsSetLoadImageNotifyRoutine_Load,
	"CmRegisterCallbackEx":                            CmRegisterCallbackEx,
	"Network_Traffic":                                 Network_Traffic,
	"File_System":                                     File_System,
	"Response_Process":                                Response_Process,
	"Response_Process_Remove":                         Response_Process_Remove,
	"Response_Network":                                Response_Network,
	"Response_Network_Remove":                         Response_Network_Remove,
	"Response_File":                                   Response_File,
	"Response_File_Remove":                            Response_File_Remove,
	"Get_Response_list":                               Get_Response_list,
	"API_HOOKING":                                     API_HOOKING,
	"Request_ALL_Monitored_Data":                      Request_ALL_Monitored_Data,
	"Request_Real_File":                               Request_Real_File,
	"Running_Process_list":                            Running_Process_list,
	"Request_PID_info":                                Request_PID_info,
	"SUCCESS":                                         SUCCESS,
	"FAIL":                                            FAIL,
	"Agent_connect":                                   Agent_connect,
	"Agent_lose_connect":                              Agent_lose_connect,
}

func (a Agent_enum) StringToAgentEnum(name string) (Agent_enum, bool) {
	value, ok := AgentEnumValues[name]
	return value, ok
}
