package parse

import (
	"CoreServer/enums"
	"CoreServer/util"
	"fmt"
	"strings"
)

type Default_Event_struct struct {
	Command enums.Agent_enum
	PID     uint64
	//SHA256      string
	//File_Path   string
	//File_Size   uint32
	//Certificate uint32
	Timestamp string
	Dyn_Data  map[string]interface{} // Command에 따라 key가 다름
}

func New_Default_Event_struct(Input_Agent_data *Deserialization_struct) *Default_Event_struct {
	// 생성자부분에서 바로 기초 데이터를 파싱한다.

	// [1/2]정적 파싱.

	Output__Default_Event_struct := Default_Event_struct{}

	Output__Default_Event_struct.Command = Input_Agent_data.Command

	Tmp_Dyn_Data := make([]interface{}, 0)

	// 기본 수집 수정
	for i, value := range Input_Agent_data.Dyn_data {
		switch i {
		case 0:
			// 1. PID
			PID := util.ERROR_PROCESSING(util.Bytes_to_UInt64(value.([]byte)))
			Output__Default_Event_struct.PID = PID
		case 1:
			// 2. Timestamp
			Timestamp := string(value.([]byte))
			Output__Default_Event_struct.Timestamp = Timestamp
		default:
			Tmp_Dyn_Data = append(Tmp_Dyn_Data, value) // 일단 Dyn_Data에 Command 별 동적 데이터를 임시로 모아둔다.
		}
	}

	// [2/2]Command에 따라 map 정보 생성
	Parsed_by_Command := make(map[string]interface{})

	// 사전 Dyn_data길이 구하기
	Dyn_Data_Length := len(Tmp_Dyn_Data)

	switch Output__Default_Event_struct.Command {
	case enums.PsSetCreateProcessNotifyRoutine_Creation_Detail:
		// PsSetCreateProcessNotifyRoutine_Creation_Detail
		if Dyn_Data_Length >= 3 {
			/*
				[0] PPID
				[1] TID
				[2] CommandLine
				[3] FILE_NAME ( exe 파일 이름 )
			*/
			// 리눅스는 4Byte, 윈도우는 handle 8byte이므로 이를 구분 해서 처리.

			// PPID
			if len(Tmp_Dyn_Data[0].([]byte)) == 4 {
				Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[0].([]byte)))
			} else if len(Tmp_Dyn_Data[0].([]byte)) == 8 {
				Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[0].([]byte)))
			}

			//Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[0].([]byte)))

			// Thread ID
			if len(Tmp_Dyn_Data[1].([]byte)) == 4 {
				Parsed_by_Command["TID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[1].([]byte)))
			} else if len(Tmp_Dyn_Data[1].([]byte)) == 8 {
				Parsed_by_Command["TID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[1].([]byte)))
			}

			//Parsed_by_Command["TID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[1].([]byte)))
			Parsed_by_Command["COMMANDLINE"] = string(Tmp_Dyn_Data[2].([]byte))
			/*
				동적

				[4] FILE_NAME ( exe 파일 이름 )
				[5] SHA256 ( exe 파일 해시)
				[6] FILE_SIZE ( exe 파일 크기 )

			*/
			//if Dyn_Data_Length >= 6 {
			Parsed_by_Command["Process_EXE_NAME"] = strings.ReplaceAll(string(Tmp_Dyn_Data[3].([]byte)), "\\\\", "\\")
			Parsed_by_Command["Process_SHA256"] = string(Tmp_Dyn_Data[4].([]byte))
			Parsed_by_Command["Process_FILE_SIZE"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[5].([]byte)))
			fmt.Printf("프로세스 생성 -> %s\n", Parsed_by_Command["Process_EXE_NAME"])
			//if Dyn_Data_Length >= 8 {
			Parsed_by_Command["Parent_EXE_NAME"] = strings.ReplaceAll(string(Tmp_Dyn_Data[6].([]byte)), "\\\\", "\\")
			Parsed_by_Command["Parent_SHA256"] = string(Tmp_Dyn_Data[7].([]byte))
			Parsed_by_Command["Parent_FILE_SIZE"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[8].([]byte)))
			//}

			//}

		}

	case enums.PsSetCreateProcessNotifyRoutine_Remove:
		// PsSetCreateProcessNotifyRoutine_Remove
		if Dyn_Data_Length == 1 {
			/*
				[0] PPID
			*/
			//Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[0].([]byte)))

			// 리눅스는 4Byte, 윈도우는 handle 8byte이므로 이를 구분 해서 처리.

			// PPID
			if len(Tmp_Dyn_Data[0].([]byte)) == 4 {
				Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[0].([]byte)))
			} else if len(Tmp_Dyn_Data[0].([]byte)) == 8 {
				Parsed_by_Command["PPID"] = util.ERROR_PROCESSING(util.Bytes_to_UInt64(Tmp_Dyn_Data[0].([]byte)))
			}
		} else {
			return nil
		}

	case enums.Network_Traffic:
		// Network_Traffic
		if Dyn_Data_Length >= 5 {
			/*
				[0] PROTOCOL_NUMBER
				[1] is_INBOUND
				[2] packet_size
				x[3] packet_buffer
				[4] Local_IP
				[5] Local_PORT
				[6] Remote_IP
				[7] Remote_PORT
			*/

			// 프로토콜 해석
			protocol_number := util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[0].([]byte)))
			protocol_name := "unknown"
			switch protocol_number {
			case 0:
				protocol_name = "HOPOPT"
			case 1:
				protocol_name = "ICMP"
			case 2:
				protocol_name = "IGMP"
			case 3:
				protocol_name = "GGP"
			case 4:
				protocol_name = "IPv4"
			case 5:
				protocol_name = "ST"
			case 6:
				protocol_name = "TCP"
			case 17:
				protocol_name = "UDP"
			case 41:
				protocol_name = "IPv6"
			case 43:
				protocol_name = "IPv6-Route"
			case 44:
				protocol_name = "IPv6-Frag"
			case 50:
				protocol_name = "ESP"
			case 51:
				protocol_name = "AH"
			case 58:
				protocol_name = "ICMPv6"
			default:
				protocol_name = fmt.Sprintf("unknown - number is -> {%d}", protocol_number)
			}

			Parsed_by_Command["PROTOCOL_NAME"] = string(protocol_name)
			Parsed_by_Command["IS_INBOUND"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[1].([]byte)))
			Parsed_by_Command["PACKET_SIZE"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[2].([]byte)))
			//Parsed_by_Command["PACKET_BUFFER"] = Tmp_Dyn_Data[3].([]byte) // []Byte 취급
			Parsed_by_Command["LOCAL_IP"] = string(Tmp_Dyn_Data[3].([]byte))
			Parsed_by_Command["LOCAL_PORT"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[4].([]byte)))
			Parsed_by_Command["REMOTE_IP"] = string(Tmp_Dyn_Data[5].([]byte))
			Parsed_by_Command["REMOTE_PORT"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[6].([]byte)))
		} else {
			return nil
		}
	case enums.CmRegisterCallbackEx:
		// CmRegisterCallbackEx
		if Dyn_Data_Length >= 2 {
			Parsed_by_Command["REGISTRY_FUNCTION"] = string(Tmp_Dyn_Data[0].([]byte))
			Parsed_by_Command["REGISTRY_OBJECT_NAME"] = string(Tmp_Dyn_Data[1].([]byte))

			if len(Tmp_Dyn_Data) >= 3 {
				if Parsed_by_Command["REGISTRY_FUNCTION"] == "RegSetValueKey" {

					Parsed_by_Command["REGISTRY_VALUE_NAME"] = string(Tmp_Dyn_Data[2].([]byte))
					Parsed_by_Command["REGISTRY_VALUE_TYPE"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[3].([]byte)))

					// 실제 Set 시 설정하려는 바이너리/데이터(없는경우도 있음)
					if len(Tmp_Dyn_Data) >= 5 {
						Parsed_by_Command["REGISTRY_VALUE_DATA"] = string(Tmp_Dyn_Data[4].([]byte))
					} else {
						Parsed_by_Command["REGISTRY_VALUE_DATA"] = ""
					}
				} else if Parsed_by_Command["REGISTRY_FUNCTION"] == "RegDeleteValueKey" {
					Parsed_by_Command["REGISTRY_VALUE_NAME"] = string(Tmp_Dyn_Data[2].([]byte))
				} else if Parsed_by_Command["REGISTRY_FUNCTION"] == "RegRenameKey" {
					Parsed_by_Command["REGISTRY_VALUE_NAME"] = string(Tmp_Dyn_Data[2].([]byte))
				}

			}

		}

	case enums.PsSetLoadImageNotifyRoutine_Load:
		{
			if Dyn_Data_Length >= 2 {
				Parsed_by_Command["Image_Path"] = strings.ReplaceAll(string(Tmp_Dyn_Data[0].([]byte)), "\\\\", "\\") // 이미지 절대경로
				Parsed_by_Command["Image_Size"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[1].([]byte)))
				Parsed_by_Command["Image_SHA256"] = string(Tmp_Dyn_Data[2].([]byte)) // 무조건 가져와야함
				//if Dyn_Data_Length >= 3 {

				//}

			}
		}
	case enums.File_System:
		{
			Parsed_by_Command["FILE_PATH"] = strings.ReplaceAll(string(Tmp_Dyn_Data[0].([]byte)), "\\\\", "\\")
			Parsed_by_Command["File_Size"] = util.ERROR_PROCESSING(util.Bytes_to_UInt32(Tmp_Dyn_Data[1].([]byte)))
			//Parsed_by_Command["File_SHA256"] = string(Tmp_Dyn_Data[2].([]byte)) // -> agent_handler.go -> check_and_Save_Binary_File() 에 처리함 (바이너리는 신중히 처리해야하므로)
			Parsed_by_Command["ACCESS_STATUS"] = string(Tmp_Dyn_Data[2].([]byte)) // DENIED -> 차단 @ GRANTED -> 허용
			Parsed_by_Command["FILE_BEHAVIOR"] = string(Tmp_Dyn_Data[3].([]byte))

			// FILE_BEAVIOR에 따른 추가 동적 데이터 대응
			if Parsed_by_Command["FILE_BEHAVIOR"] == "Rename" {
				// Rename인 경우, 바뀔 파일명이 추가된다.
				Parsed_by_Command["FILE_RENAME_FILE_PATH"] = strings.ReplaceAll(string(Tmp_Dyn_Data[4].([]byte)), "\\\\", "\\")

			}
		}
	default:
		// 알 수 없는 경우
		return nil
	}

	// 동적 데이터 반영
	Output__Default_Event_struct.Dyn_Data = Parsed_by_Command

	return &Output__Default_Event_struct

}
