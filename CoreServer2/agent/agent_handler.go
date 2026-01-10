package agent

import (
	analysisserver "CoreServer/AnalysisServer"
	SIEM "CoreServer/SIEM"
	ShareObject "CoreServer/Share_Object"
	"CoreServer/Socket"
	agent_manager "CoreServer/agent_management"
	processmanagement "CoreServer/agent_management/process_management"
	"CoreServer/enums"
	"CoreServer/parse"
	"CoreServer/util"
	"fmt"
	"net"
	"sync"
)

/*
	본 Go 코드는 ...
	연결된 에이전트의 TCP연결을 수신후, "별도의 비동기 스레드"를 위한 구조체를 정의한다.

	다음과 같은 기능이 있다.
	1. 항상 에이전트에게 TCP명령을 주기적으로 요청한다.
	2. 에이전트로부터 받은  패킷을 파싱처리한다.
	3. 얻은 데이터는 에이전트의 프로세스 기반 행위 추적 구조체로 저장/관리한다.
*/

type Agent_Manager struct {
	//Agent_ID string // SHA512 ( 출처: 엔드포인트의 SMBIOS type 0 + SMBIOS type 1 한 값의 SHA512 )

	shareobject *ShareObject.Sharing

	Agent_Controller *agent_manager.Agent_Controller

	mutex_ *sync.Mutex

	mutex__ *sync.Mutex
}

// 생성자 부분
func New_Agent_Manager(TCPconn net.Conn, shareobject *ShareObject.Sharing, Seedobject *util.Seed) *Agent_Manager {

	agent_socket := Socket.New_Agent_Socket(TCPconn)

	return &Agent_Manager{

		shareobject: shareobject,

		Agent_Controller: agent_manager.New_Agent_Controller(agent_socket, Seedobject), // 명령 세트

		mutex_:  &sync.Mutex{},
		mutex__: &sync.Mutex{},
	}
}

// 핵심 부분
func (as *Agent_Manager) Start_Agent_Communication() {

	/*
		시작전,,,,, 초기통신
		1. AGENT_ID 얻기
		2. 분석서버에 AGENT_ID 전달하기 (중복전달일지라도,,)
	*/
	if !as.Agent_Controller.Initial_Communication() { // 초기통신 수행
		as.shareobject.Remove_Agent_Controller(as.Agent_Controller)
		return // 에이전트간 세션 종료
	}

	// 연결된 이벤트를 전달
	//as.send_agent_status(enums.Agent_connect)

	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////
	///////////////////////////////////////////////////////////////////////////////////////////////

	// DB에 에이전트 목록 추가 ( 새로운 에이전트일 때 테이블에 추가됨)
	//as.core_server_manager.Share_obj.DB_Manager.InsertAgent_2_DB(as.Agent_ID, as.Agent_info["OS_info"].(string), strings.Split(as.Agent_TCP.TCPconn.RemoteAddr().String(), ":")[0])

	/*
		무한 루프
	*/
	fmt.Print("Agent와 연결되었습니다.")

	// 하위 루프는 상당히 빠르게 진행되어야한다.
	for {

		//if recv_data, _ := as.loop_request_to_Agent(); recv_data != nil {
		if recv_data, _ := as.Agent_Controller.Loop_request_to_Agent(); recv_data != nil {

			// 빈 껍데기를 가져왔는 지 확인해야함
			if recv_data[0].Command == enums.FAIL {
				continue
			}

			if !as.Agent_Controller.Agent_TCP.Is_Disconnected {

				// go루틴 병렬 파싱/솔루션 전송 처리

				dataCopy := append([]parse.Deserialization_struct(nil), recv_data...) // 데이터 Copy
				go as.send_agent_log(dataCopy)

			}

		} else {
			// loop 데이터 요청 실패
			fmt.Println("에이전트에게 데이터를 전송하지 못했습니다. <<연결을 끊겠습니다.>>")

			// 연결끊김 이벤트를 전달
			//as.send_agent_status(enums.Agent_lose_connect)

			as.shareobject.Remove_Agent_Controller(as.Agent_Controller)
			return // 에이전트간 세션 종료
		}

	}
}

// /////////////////////////////////////////////////////////////////////////////////////////////////////////////
// /////////////////////////////////////////////////////////////////////////////////////////////////////////////
// /////////////////////////////////////////////////////////////////////////////////////////////////////////////

// 에이전트 로그 처리 후 솔루션 전송 [go-routine]
func (as *Agent_Manager) send_agent_log(recv_data []parse.Deserialization_struct) {

	// send_agent_log 스레드는 모두 작업 완료까지 블로킹 시간이 길다. mutex로 순차적으로 진행하도록 하여 프로세스 생성 및 생애주기 순서를 보장하도록 한다.
	as.mutex__.Lock()
	defer as.mutex__.Unlock()

	// 2차원 구조를 1차원씩 꺼내서 리스트 map 생성
	for _, event := range recv_data {

		if as.Agent_Controller.Agent_TCP.Is_Disconnected {
			return
		}

		// 실패 반환하면 continue
		if event.Command == enums.FAIL {
			continue
		} else {
			// 프로세스 매니저.go가 이벤트를 쉽게 처리할 수 있도록 변환필요 ( 여기는 각 Command마다 수동처리해야한다 )
			if parsed_event := parse.New_Default_Event_struct(&event); parsed_event != nil {
				////////////////////////////////////////////////////////////////////
				////////////////////////////////////////////////////////////////////

				// 1. 프로세스 "생성 시" 사용자가 실제 클릭해서 실행했는 지 여부 파싱하기 ( Output_Process_Life_Cycle_infos 에 편입됨 )
				// 2. 일관성이 있는 프로세스 정보를 위한 "사이클" 정보 가져오기
				cycle_, err := as.Agent_Controller.Output_Process_Life_Cycle_infos(parsed_event)
				if err != nil {
					continue // 사이클을 정상적으로 가져오기 못한 경우
				}

				// 실제 바이너리 요청 후 분석서버 요청 메서드 -> :: 바이너리 관련한 처리는 여기서 다함 + "파일타입" 분석 서버 요청 포함
				/*
					as.check_and_Save_Binary_File(
						parsed_event.Command,   // 이벤트 종류 인자
						parsed_event,           // 이벤트 구조체 인자
						&parsed_event.Dyn_Data, // Dyn_Data 인자에 새로운 key를 삽입할 수 있음(sha256 키 추가)
					)

					// 네트워크 유형일 떄 remote_ip 분석서버에 분석 요청
					if parsed_event.Command == enums.Network_Traffic {
						go as.check_network_analysis(parsed_event.Dyn_Data["REMOTE_IP"].(string))
					}

				*/
				// 이벤트 1개 -> ElasticSearch index 규격 JSON생성 -> 카프카 전송
				as.send_to_elastic_search(
					parsed_event.Command,
					uint32(parsed_event.PID),
					parsed_event.Timestamp,
					*cycle_,
					parsed_event.Dyn_Data,
				)

			} else {
				fmt.Println("이벤트 변환 실패!")

				// 연결끊김 이벤트를 전달
				//as.send_agent_status(enums.Agent_lose_connect)

				as.shareobject.Remove_Agent_Controller(as.Agent_Controller)
				return // 에이전트간 스레드 종료
			}
		}
	}
}

/*




 */
// go routine 사후 처리 ( get FILE --> Elasticsearch 저장 )

// 바이너리 정보를 DB에 저장한다 ( 체크 후 저장 )

func (as *Agent_Manager) check_and_Save_Binary_File(
	cmd enums.Agent_enum,
	parsed_event *parse.Default_Event_struct,
	Inout_Dyn_Data *map[string]interface{}, // 3번쨰 인자 "Inout_Dyn_Data" 이것은 SHA256를 Dyn_Data에 추가할 때, 동적으로 넣어주는 것임 -> 결국 Dyn_Data에 SHA256키가 생성되는 것 (필수단계)
) bool {
	// cmd 에서 실제 파일 경로가 있는 enum값을 가져와서 파일명과 크기를 가져와서 DB에 저장한다.
	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	switch cmd {
	case enums.PsSetCreateProcessNotifyRoutine_Creation_Detail:
		{
			Process_EXE_NAME := string(parsed_event.Dyn_Data["Process_EXE_NAME"].(string))
			Process_FILE_SIZE := uint32(parsed_event.Dyn_Data["Process_FILE_SIZE"].(uint32))

			Parent_EXE_NAME := string(parsed_event.Dyn_Data["Parent_EXE_NAME"].(string))
			Parent_FILE_SIZE := uint32(parsed_event.Dyn_Data["Parent_FILE_SIZE"].(uint32))

			go as.save_Binary_File(Process_EXE_NAME, Process_FILE_SIZE, true)
			go as.save_Binary_File(Parent_EXE_NAME, Parent_FILE_SIZE, true)

		}
	case enums.PsSetLoadImageNotifyRoutine_Load:
		{
			Image_PATH := string(parsed_event.Dyn_Data["Image_Path"].(string))
			Image_SIZE := uint32(parsed_event.Dyn_Data["Image_Size"].(uint32))

			go as.save_Binary_File(Image_PATH, Image_SIZE, true)
		}
	case enums.File_System:
		{
			File_PATH := string(parsed_event.Dyn_Data["FILE_PATH"].(string))
			File_SIZE := uint32(parsed_event.Dyn_Data["File_Size"].(uint32))

			//as.save_Binary_File(File_PATH, File_SIZE)

			(*Inout_Dyn_Data)["File_SHA256"] = as.save_Binary_File(File_PATH, File_SIZE, false) // SHA256 생성 (파일에 대한)
		}
	default:
		return false
	}
	return true
}

// 실제 바이너리를 에이전트에 요청하고 DB(정보) +  binary(실제 coreserver가 위치한 스토리지) 2가지를 저장 하고 "반환"하는 것
func (as *Agent_Manager) save_Binary_File(file_path_on_endpoint string, fileSize uint32, is_request_to_analysis bool) string {

	sha256 := ""

	if !as.shareobject.Database.Check_exists_Binary_File(as.Agent_Controller.Output_AGENT_ID(), file_path_on_endpoint, fileSize) {

		if binary, _, err := as.Agent_Controller.Request_Real_File(file_path_on_endpoint); err == nil {
			sha256 = util.Hash_to_String(util.Get_SHA256(binary))
			// 실제 바이너리 쓰기
			as.shareobject.FileIo.Write_File(sha256, binary, true)

			as.shareobject.Database.Insert_Binary_File(as.Agent_Controller.Output_AGENT_ID(), file_path_on_endpoint, as.shareobject.FileIo.Root_Dir+"/"+sha256, fileSize, sha256)

		} else {
			fmt.Print("바이너리 받지 못했습니다.-> 연결종료\n")
			as.Agent_Controller.Agent_TCP.Disconnect()
		}

	} else {
		// 이미 DB에 존재하는 경우
		sha256 = as.shareobject.Database.Output_Binary_File_SHA256_from_CoreServer(as.Agent_Controller.Output_AGENT_ID(), file_path_on_endpoint, fileSize)

	}

	// 이걸로 분석 서버 요청 로직 변경
	// 1. sha256넘겨 확인
	// 2. (1) 시 분석 결과 없으면 요청
	as.check_file_analysis(sha256)
	return sha256
}

/*
분석 서버에 분석 요청 (설정상 비동기 요청) -> 응답 처리 안하므로,,,
*/
func (as *Agent_Manager) check_file_analysis(sha256 string) {

	// sha256를 분석서버에 먼저 전달하고 분석 결과가 없으면 요청
	if as.shareobject.AnalysisServer_Manager.Check_Analysis_Result_SHA256(sha256) == false {
		// 이 경우, 분석 서버 결과가 없다는 것을 확인.
		// local storage에서 바이너리 가져와 분석 요청진행.

		if binary, err := as.shareobject.FileIo.Read_File(sha256); err == nil {
			if base64 := util.Bytes_to_Base64(binary); err == nil {
				if filesize := uint32(len(binary)); err == nil {
					go as.request_file_analysis(base64, filesize, sha256) // 분석 전달
				}
			}
		}
	}
}

func (as *Agent_Manager) request_file_analysis(base64 string, filesize uint32, sha256 string) {

	// sha256전달 후 분석 완료되었는 지 확인  (force_mode인 경우 강제 분석요청(업데이트 됨))

	// 분석 서버에 (파일) 분석 요청
	as.shareobject.AnalysisServer_Manager.Request_Analysis(analysisserver.Request_Analysis_struct{
		SCRIPT_TYPE: analysisserver.FileType,
		DATA: analysisserver.Request_Analysis_Data{
			Base64Bin: base64,
			FileSize:  filesize,
			Sha256:    sha256,
			Remote_ip: "",
		},
	})
}

// 네트워크 분석
func (as *Agent_Manager) check_network_analysis(remote_ip string) {

	if as.shareobject.AnalysisServer_Manager.Check_Analysis_Result_remote_ip(remote_ip) == false {
		// 이 경우, 분석 서버 결과가 없다는 것을 확인.
		go as.request_remote_ip_analysis(remote_ip) // 분석 전달
	}
}
func (as *Agent_Manager) request_remote_ip_analysis(remote_ip string) {
	// 분석 서버에 (파일) 분석 요청
	as.shareobject.AnalysisServer_Manager.Request_Analysis(analysisserver.Request_Analysis_struct{
		SCRIPT_TYPE: analysisserver.NetworkType,
		DATA: analysisserver.Request_Analysis_Data{
			Base64Bin: "",
			FileSize:  0,
			Sha256:    "",
			Remote_ip: remote_ip,
		},
	})
}

//

// 엘라스틱 서치에 전달 (사실은 카프카에게 ..)
func (as *Agent_Manager) send_to_elastic_search(
	cmd enums.Agent_enum,
	//
	PID uint32,
	timestamp string,
	//
	cycle_info processmanagement.Cycle_Info,
	//
	Dyn_Data map[string]interface{}, // 동적 데이터 (cmd에따라 다름)
) bool {

	switch cmd {
	case enums.PsSetCreateProcessNotifyRoutine_Creation_Detail:
		{
			//fmt.Printf("프로세스 실행 -> %v @@@@ %v \n 사이클 정보'자신': %v '직계부모': %v \n\n ", Dyn_Data["Process_EXE_NAME"].(string), Dyn_Data["Process_SHA256"].(string), cycle_info.My_cycle_info.Process_life_cycle_id, cycle_info.My_cycle_info.My_parent_Process_life_cycle_id)

			if !cycle_info.My_cycle_info.Is_child {
				// Root 프로세스
				as.send_Create_ProcessEvent(
					SIEM.Unique_Behavior_Process_Created_Event{
						ProcessId:            fmt.Sprint(PID),
						ProcessSHA256:        Dyn_Data["Process_SHA256"].(string),
						ImagePath:            Dyn_Data["Process_EXE_NAME"].(string),
						ImageSize:            Dyn_Data["Process_FILE_SIZE"].(uint32),
						CommandLine:          Dyn_Data["COMMANDLINE"].(string),
						Parent_ProcessSHA256: Dyn_Data["Parent_SHA256"].(string),
						Parent_ImagePath:     Dyn_Data["Parent_EXE_NAME"].(string),
						Parent_ImageSize:     Dyn_Data["Parent_FILE_SIZE"].(uint32),
					},
					*cycle_info.My_cycle_info,
					timestamp,
				)
			} else {
				// 자식프로세스 알림 ( 직계 부모 측면 )
				as.send_Create_Child_ProcessEvent(
					SIEM.Unique_Behavior_Child_Process_Created_Event{
						Child_ProcessId:     fmt.Sprint(PID),
						Child_ProcessSHA256: Dyn_Data["Process_SHA256"].(string),
						Child_ImagePath:     Dyn_Data["Process_EXE_NAME"].(string),
						Child_ImageSize:     Dyn_Data["Process_FILE_SIZE"].(uint32),
						Child_CommandLine:   Dyn_Data["COMMANDLINE"].(string),
					},
					*cycle_info.My_cycle_info,        // 내가 가진 사이클 정보
					*cycle_info.My_Parent_cycle_info, // 부모가 가진 사이클 정보 제공
					timestamp,
				)

				// 자기 자신 생성 알림
				as.send_Create_ProcessEvent(
					SIEM.Unique_Behavior_Process_Created_Event{
						ProcessId:            fmt.Sprint(PID),
						ProcessSHA256:        Dyn_Data["Process_SHA256"].(string),
						ImagePath:            Dyn_Data["Process_EXE_NAME"].(string),
						ImageSize:            Dyn_Data["Process_FILE_SIZE"].(uint32),
						CommandLine:          Dyn_Data["COMMANDLINE"].(string),
						Parent_ProcessSHA256: Dyn_Data["Parent_SHA256"].(string),
						Parent_ImagePath:     Dyn_Data["Parent_EXE_NAME"].(string),
						Parent_ImageSize:     Dyn_Data["Parent_FILE_SIZE"].(uint32),
					},
					*cycle_info.My_cycle_info, // 내가 가진 사이클 정보 제공
					timestamp,
				)
			}

		}
	case enums.PsSetCreateProcessNotifyRoutine_Remove:
		{
			as.send_Process_Terminated_Event(
				*cycle_info.My_cycle_info,
				timestamp,
			)
		}
	case enums.Network_Traffic:
		{
			REMOTE_IP := Dyn_Data["REMOTE_IP"].(string)

			ip_info, _ := util.Get_IP_info(REMOTE_IP)
			if ip_info == nil {

				return false
			}

			//fmt.Printf("GET_IP_INFO -> %v \n", ip_info)

			// 내부적 처리

			// 바운드
			IS_INBOUND := Dyn_Data["IS_INBOUND"].(uint32)
			Direction := ""
			if IS_INBOUND > 0 {
				Direction = "Inbound"
			} else {
				Direction = "Outbound"
			}

			as.send_Network_Event(
				SIEM.Unique_Behavior_network_Event{
					Remote_IP:   Dyn_Data["REMOTE_IP"].(string),
					Remote_Port: Dyn_Data["REMOTE_PORT"].(uint32),
					Protocol:    Dyn_Data["PROTOCOL_NAME"].(string),
					Direction:   Direction,
					PacketSize:  Dyn_Data["PACKET_SIZE"].(uint32),
					Geoip: SIEM.Unique_Geoip_Event{
						Ip:         REMOTE_IP,
						Country:    ip_info.Country,
						Region:     ip_info.Region,
						RegionName: ip_info.RegionName,
						TimeZone:   ip_info.Timezone,
						City:       ip_info.City,
						Zip:        ip_info.Zip,
						Isp:        ip_info.Isp,
						Org:        ip_info.Org,
						As:         ip_info.As,
						Location: SIEM.ElasticSearch_geo_point{
							Lat: ip_info.Lat,
							Lon: ip_info.Lon,
						},
					},
				},
				*cycle_info.My_cycle_info,
				timestamp,
			)
		}
	case enums.CmRegisterCallbackEx:
		{
			as.send_Registry_Event(
				SIEM.Unique_Behavior_registry_Event{
					RegistryObjectName: Dyn_Data["REGISTRY_OBJECT_NAME"].(string),
					RegistryKey:        Dyn_Data["REGISTRY_FUNCTION"].(string),
				},
				*cycle_info.My_cycle_info,
				timestamp,
			)
		}
	case enums.PsSetLoadImageNotifyRoutine_Load:
		{
			as.send_Image_Load_Event(
				SIEM.Unique_Behavior_image_load_Event{
					ImageFullPath: Dyn_Data["Image_Path"].(string),
					SHA256:        Dyn_Data["Image_SHA256"].(string),
					Size:          Dyn_Data["Image_Size"].(uint32),
				},
				*cycle_info.My_cycle_info,
				timestamp,
			)
		}
	case enums.File_System:
		{
			if _, ok := Dyn_Data["File_SHA256"]; !ok {
				return false
			}

			as.send_File_System_Event(
				SIEM.Unique_Behavior_file_system_Event{
					FilePath:   Dyn_Data["FILE_PATH"].(string),
					Size:       Dyn_Data["File_Size"].(uint32),
					FileSha256: Dyn_Data["File_SHA256"].(string),
					Action:     Dyn_Data["FILE_BEHAVIOR"].(string),
				},
				*cycle_info.My_cycle_info,
				timestamp,
			)
		}
	default:
		return false // 알 수 없는 경우
	}
	return true
}

// 프로세스 생성
func (as *Agent_Manager) send_Create_ProcessEvent(event SIEM.Unique_Behavior_Process_Created_Event, cycle processmanagement.Basic_cycle_info, Timestamp string) {
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"Process_Created": map[string]interface{}{
					"ProcessId":            event.ProcessId,
					"ProcessSHA256":        event.ProcessSHA256,
					"ImagePath":            event.ImagePath,
					"ImageSize":            event.ImageSize,
					"CommandLine":          event.CommandLine,
					"Parent_ProcessSHA256": event.Parent_ProcessSHA256,
					"Parent_ImagePath":     event.Parent_ImagePath,
					"Parent_ImageSize":     event.Parent_ImageSize,
				},
			},
		},
	}
	as.send_log(log)
}

// 자식 생성
func (as *Agent_Manager) send_Create_Child_ProcessEvent(event SIEM.Unique_Behavior_Child_Process_Created_Event, my_cycle processmanagement.Basic_cycle_info, parent_cycle processmanagement.Basic_cycle_info, Timestamp string) {

	// 이 이벤트의 주체는 (자신의 부모)에 해당하는 이벤트를 발송
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(parent_cycle.Process_life_cycle_id, parent_cycle.My_parent_Process_life_cycle_id, parent_cycle.Root_parent_Process_life_cycle_id, parent_cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"Child_Process_Created": map[string]interface{}{
					"Child_ProcessId":             event.Child_ProcessId,
					"Child_ProcessSHA256":         event.Child_ProcessSHA256,
					"Child_ImagePath":             event.Child_ImagePath,
					"Child_ImageSize":             event.Child_ImageSize,
					"Child_CommandLine":           event.Child_CommandLine,
					"Child_Process_Life_Cycle_Id": my_cycle.Process_life_cycle_id,
				},
			},
		},
	}

	as.send_log(log)
}

// 파일 시스템
func (as *Agent_Manager) send_File_System_Event(event SIEM.Unique_Behavior_file_system_Event, cycle processmanagement.Basic_cycle_info, Timestamp string) {
	//fmt.Printf("send_File_System_Event -> %v", event)
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"file_system": map[string]interface{}{
					"FilePath": event.FilePath,
					"FileSize": event.Size,
					"Action":   event.Action,
				},
			},
		},
	}

	as.send_log(log)
}

// 네트워크
func (as *Agent_Manager) send_Network_Event(event SIEM.Unique_Behavior_network_Event, cycle processmanagement.Basic_cycle_info, Timestamp string) {
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"network": map[string]interface{}{
					"RemoteIp":   event.Remote_IP,
					"RemotePort": event.Remote_Port,
					"Protocol":   event.Protocol,
					"Direction":  event.Direction,
					"PacketSize": event.PacketSize,
					"geoip": map[string]interface{}{
						"Ip":         event.Geoip.Ip,
						"Country":    event.Geoip.Country,
						"Region":     event.Geoip.Region,
						"RegionName": event.Geoip.RegionName,
						"TimeZone":   event.Geoip.TimeZone,
						"City":       event.Geoip.City,
						"Zip":        event.Geoip.Zip,
						"Isp":        event.Geoip.Isp,
						"Org":        event.Geoip.Org,
						"As":         event.Geoip.As,
						"location": map[string]float64{
							"lat": event.Geoip.Location.Lat,
							"lon": event.Geoip.Location.Lon,
						},
					},
				},
			},
		},
	}
	as.send_log(log)
}

// 레지스트리
func (as *Agent_Manager) send_Registry_Event(event SIEM.Unique_Behavior_registry_Event, cycle processmanagement.Basic_cycle_info, Timestamp string) {
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"registry": map[string]interface{}{
					"RegistryObjectName": event.RegistryObjectName,
					"RegistryKey":        event.RegistryKey,
				},
			},
		},
	}
	as.send_log(log)
}

// 프로세스 종료
func (as *Agent_Manager) send_Process_Terminated_Event(cycle processmanagement.Basic_cycle_info, Timestamp string) {
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"Process_Terminated": map[string]interface{}{
					"Timestamp": Timestamp,
				},
			},
		},
	}
	as.send_log(log)
}

// 이미지 로드
func (as *Agent_Manager) send_Image_Load_Event(event SIEM.Unique_Behavior_image_load_Event, cycle processmanagement.Basic_cycle_info, Timestamp string) {
	log := map[string]interface{}{
		"common":      as.get_common_event(Timestamp),
		"categorical": as.get_categorical_event(cycle.Process_life_cycle_id, cycle.My_parent_Process_life_cycle_id, cycle.Root_parent_Process_life_cycle_id, cycle.Root_is_running_by_user),

		"unique": map[string]interface{}{
			"process_behavior_events": map[string]interface{}{
				"image_load": map[string]interface{}{
					"ImagePath":   event.ImageFullPath,
					"ImageSHA256": event.SHA256,
					"ImageSize":   event.Size,
				},
			},
		},
	}
	as.send_log(log)
}

// 카프카에게 전달
func (as *Agent_Manager) send_log(event map[string]interface{}) {
	go as.shareobject.Kafka_Manager.Send_to_Kafka(event)
}

// / 로그 묶음
func (as *Agent_Manager) get_categorical_event(
	Process_Life_Cycle_ID string, Parent_Process_Life_Cycle_Id string, Root_Parent_Process_Life_Cycle_Id string, Root_is_running_by_user bool,
) map[string]interface{} {
	return SIEM.Get_categorical_event(
		as.Agent_Controller.Output_AGENT_ID(), as.Agent_Controller.Output_AGENT_INFO()["OS_info"].(string),
		Process_Life_Cycle_ID, Parent_Process_Life_Cycle_Id, Root_Parent_Process_Life_Cycle_Id, Root_is_running_by_user,
	)
}

func (as *Agent_Manager) get_common_event(Timestamp string) map[string]interface{} {
	return SIEM.Get_common_event(
		as.Agent_Controller.Output_AGENT_INFO()["Local_IP"].(string),
		as.Agent_Controller.Output_AGENT_INFO()["Mac_Address"].(string),
		Timestamp,
	)
}
