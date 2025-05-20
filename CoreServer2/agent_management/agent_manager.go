package agent_manager

import (
	"CoreServer/Socket"
	processManager "CoreServer/agent_management/process_management"
	"CoreServer/enums"
	"CoreServer/parse"
	"CoreServer/util"
	"fmt"
	"strings"
	"sync"
)

type Agent_Controller struct {
	Agent_TCP                *Socket.Agent_Socket
	agent_info               map[string]interface{}
	processManager           *processManager.Process_Manager
	process_Life_Cycle_mutex *sync.Mutex
}

func New_Agent_Controller(Agent_TCP *Socket.Agent_Socket, Seedobject *util.Seed) *Agent_Controller {

	agent_info := map[string]interface{}{

		"Agent_ID":                         "",
		"OS_info":                          "",
		"Local_IP":                         "",
		"Mac_Address":                      "",
		"Agent_Source_IP":                  Agent_TCP.TCPconn.RemoteAddr().String(),
		"Connected_Timstamp_by_Agent_Time": "",
		"Status":                           "connected",
	}

	return &Agent_Controller{
		Agent_TCP:                Agent_TCP,
		agent_info:               agent_info,
		processManager:           processManager.New_Process_Manager(Seedobject),
		process_Life_Cycle_mutex: &sync.Mutex{},
	}
}

// 0. 연결 초기화 작업
// 초기 작업
func (as *Agent_Controller) Initial_Communication() bool {

	if recv_data, err := as.Agent_TCP.Receive(); err != nil {
		// 실패
		fmt.Println("AGENT_ID를 못얻음!  <<연결을 끊겠습니다.>>")
		as.Agent_TCP.Disconnect()
		return false
	} else {
		// 실패
		if len(recv_data) < 1 {
			fmt.Println("AGENT_ID 길이가 만족하지 않습니다.!   <<연결을 끊겠습니다.>>")
			as.Agent_TCP.Disconnect()
			return false
		} else {
			// 성공 ( 바이너리 SMBIOS 데이터 덩어리를 SHA512로 변환하여 에이전트 식별 관리(offline and online) )

			if recv_data_parse, err1 := parse.To_Deserialization(recv_data); err1 == nil {

				// 1. 에이전트 ID 등록
				SMBIOS := recv_data_parse[0].Dyn_data[0].([]byte) // SMBIOS type 1+ 2 더한 바이트 값
				AGENT_ID_byte := util.Get_SHA512(SMBIOS)          // To []byte -> SHA512( []byte )
				AGENT_ID := util.Hash_to_String(AGENT_ID_byte)    // To SHA512( []byte ) -> string
				as.agent_info["Agent_ID"] = AGENT_ID
				fmt.Printf("AGENT_ID를 얻음! %v \n", as.agent_info["Agent_ID"])

				// 2. OS_info 등록
				OS_info := string(recv_data_parse[0].Dyn_data[1].([]byte))
				as.agent_info["OS_info"] = OS_info

				Local_IP := string(recv_data_parse[0].Dyn_data[2].([]byte))
				as.agent_info["Local_IP"] = Local_IP

				Mac_Address := strings.ReplaceAll(string(recv_data_parse[0].Dyn_data[3].([]byte)), "-", ":")
				as.agent_info["Mac_Address"] = Mac_Address

				as.agent_info["Connected_Timstamp_by_Agent_Time"] = string(recv_data_parse[0].Dyn_data[4].([]byte)) // 항상 마지막에 전달하는 타임스탬프 임

				// 3. 연결상태
				as.agent_info["Status"] = "connected"

				/* 분석 서버에 에이전트 ID를 추가해야한다.  */
				//as.core_server_manager.Share_obj.Policy.Analysis_Policy.Add_Agent_ID(&as.Agent_ID)

			} else {
				return false
			}

		}
	}
	return true
}

// 1. 수집된 데이터 모두 가져오기
func (as *Agent_Controller) Loop_request_to_Agent() ([]parse.Deserialization_struct, error) {

	return as.send_2_Agent(
		enums.Request_ALL_Monitored_Data,
		[]interface{}{
			"give me that!!", // 사실 무의미하지만, 로직상 1개이상의 데이터를 전달해야함
		},
	)

}

// 2. 바이너리 파일 요청
func (as *Agent_Controller) Request_Real_File(absolute_file_path string) ([]byte, string, error) {

	parsed, err := as.send_2_Agent(
		enums.Request_Real_File,
		[]interface{}{
			absolute_file_path, // 요청할 문자열 (맨뒤 0x00 필요)
		},
	)
	if err == nil {
		if parsed[0].Command == enums.SUCCESS {

			file_bin := []byte(parsed[0].Dyn_data[0].([]byte))

			return file_bin, util.Bytes_to_Base64(file_bin), nil
		}
	}
	return []byte{}, "", err
}

// 부수적 기능
func (as *Agent_Controller) Output_AGENT_ID() string {
	return string(as.agent_info["Agent_ID"].(string))
}
func (as *Agent_Controller) Output_AGENT_STATUS() string {
	return as.agent_info["Status"].(string)
}
func (as *Agent_Controller) Output_AGENT_INFO() map[string]interface{} {
	return as.agent_info
}

// 프로세스 라이프 사이클 ID 반환
func (as *Agent_Controller) output_Process_Life_Cycle_ID(PID uint64, PPID uint64, cmd enums.Agent_enum, is_running_by_user bool) (*processManager.Cycle_Info, error) {

	as.process_Life_Cycle_mutex.Lock()
	defer as.process_Life_Cycle_mutex.Unlock()

	if cmd == enums.PsSetCreateProcessNotifyRoutine_Creation_Detail {
		// 프로세스 생성 시 (부모 또는 자식이 생길 수 있음)
		return as.processManager.Get_process_life_cycle_ID_with_PPID(PID, PPID, is_running_by_user, true)

	} else if cmd == enums.PsSetCreateProcessNotifyRoutine_Remove {
		// 이 경우의 위험성은 아직 배열에 없는 프로세스가 종료를 요청한 경우,
		cycle_, err := as.processManager.Get_process_life_cycle_ID_with_PPID(PID, PPID, is_running_by_user, false)
		if err == nil {
			as.processManager.Set_process_terminate(PID)
			return cycle_, nil
		} else {
			return nil, err
		}

	} else {
		// 이 경우의 위험성은 "부모보다 자식이 먼저"올 수 있다는 위험이 있다.
		return as.processManager.Get_process_life_cycle_ID(PID)
	}
}

// 사용자 실행 여부
func (as *Agent_Controller) is_running_process_by_real_user_WHEN_process_created(parsed_event *parse.Default_Event_struct) bool {
	is_running_by_user := false
	if parsed_event.Command == enums.PsSetCreateProcessNotifyRoutine_Creation_Detail {

		if strings.Contains(parsed_event.Dyn_Data["Parent_EXE_NAME"].(string), "explorer.exe") {
			fmt.Printf("사용자에 의해 실행된 프로세스 입니다.")
			is_running_by_user = true
		}
	}

	return is_running_by_user
}

// 사이클 정보 가져오기
func (as *Agent_Controller) Output_Process_Life_Cycle_infos(parsed_event *parse.Default_Event_struct) (*processManager.Cycle_Info, error) {

	is_running_by_user := as.is_running_process_by_real_user_WHEN_process_created(parsed_event) // 실제 사용자가 실행한 루트 프로세스인가?

	PPID := uint64(0)
	if parsed_event.Command == enums.PsSetCreateProcessNotifyRoutine_Creation_Detail ||
		parsed_event.Command == enums.PsSetCreateProcessNotifyRoutine_Remove {

		PPID = parsed_event.Dyn_Data["PPID"].(uint64)
	}

	// PID/사이클 찾기
	return as.output_Process_Life_Cycle_ID(parsed_event.PID, PPID, parsed_event.Command, is_running_by_user)

}

/*
func (as *Agent_Controller) Send_agent_status(agent_connection_status enums.Agent_enum) {
	// 연결된 이벤트를 전달
	agent_connected_event := map[string]interface{}{
		"agent_info":          as.Output_AGENT_INFO(),
		"command":             util.ERROR_PROCESSING(agent_connection_status.String()), // command에 따라 연결상태 확인 ( connected 또는 lose)
		"timestamp_by_agent":  as.Output_AGENT_INFO()["Connected_Timstamp_by_Agent_Time"],
		"timestamp_by_server": util.ERROR_PROCESSING(util.GetTimestamp_iso8601()), // 서버에서 받은 타임스탬프
	}
	as.shareobject.RegisteredServer_Manager.Send_list_map([]map[string]interface{}{agent_connected_event})
}*/

// Response
func (as *Agent_Controller) Process_Response(SHA256 string, FileSize uint32, is_remove bool) bool {
	var cmd = enums.Agent_enum(0)
	if is_remove {
		cmd = enums.Response_Process_Remove
	} else {
		cmd = enums.Response_Process
	}

	// response
	if result, err := as.send_2_Agent(cmd, []interface{}{SHA256, FileSize}); err == nil {
		fmt.Print(result)
		return true
	} else {
		return false
	}
}

func (as *Agent_Controller) File_Response(SHA256 string, FileSize uint32, is_remove bool) bool {
	var cmd = enums.Agent_enum(0)
	if is_remove {
		cmd = enums.Response_File_Remove
	} else {
		cmd = enums.Response_File
	}

	// response
	if result, err := as.send_2_Agent(cmd, []interface{}{SHA256, FileSize}); err == nil {
		fmt.Print(result)
		return true
	} else {
		return false
	}
}

func (as *Agent_Controller) Network_Response(remoteip string, is_remove bool) bool {
	var cmd = enums.Agent_enum(0)
	if is_remove {
		cmd = enums.Response_Network_Remove
	} else {
		cmd = enums.Response_Network
	}

	// response
	if result, err := as.send_2_Agent(cmd, []interface{}{remoteip}); err == nil {
		fmt.Print(result)
		return true
	} else {
		return false
	}
}

func (as *Agent_Controller) send_2_Agent(Cmd enums.Agent_enum, Dyn_data []interface{}) ([]parse.Deserialization_struct, error) {

	// 요청 데이터 생성
	send_to_agent := parse.Deserialization_struct{
		Command:  Cmd, // 지금까지 에이전트가 모은 데이터를 가져오도록 요구명령.
		Dyn_data: Dyn_data,
	}

	// 이후 요청하고, 역직렬화 결과 받기
	if recv_data, err := as.Agent_TCP.Send_Agent_Command(&send_to_agent); err == nil {

		return recv_data, nil
		// 성공일 때
		/*
			if recv_data[0].Command == enums.SUCCESS {

				if output != nil {
					*output = recv_data[0].Dyn_data
				}
				return true

			}
		*/
	} else {
		return nil, fmt.Errorf("명령 전송 실패")
	}
}
