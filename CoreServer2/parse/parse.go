package parse

import (
	"CoreServer/enums"
	"CoreServer/util"
	"bytes"
	"fmt"
)

type Deserialization_struct struct {
	Command  enums.Agent_enum // "맨 앞에서 8바이트 위치"
	Dyn_data []interface{}    // 여러 타입의 데이터를 내포함 ("_END" 4b 제외) ( 2차원 구조 )
}

// 직렬화 ( 구조화된 데이터 --> 하나의 바이트)
func To_Serialization(De_data Deserialization_struct) ([]byte, error) {

	// byte 버퍼 준비.
	return_byte_buffer := new(bytes.Buffer)

	// [1/3]command 삽입
	cmd, err := util.Int32_to_Bytes(int32(De_data.Command))
	if err != nil {
		return nil, err
	} else {
		return_byte_buffer.Write(cmd)
	}

	// 하나씩 순회하여 '타입을 확인후' 직렬화한다.
	// [2/3]각 item-value들은 리틀 엔디언이며, 항상 앞에 4바이트 길이를 가진다.
	for _, value := range De_data.Dyn_data {
		switch v := value.(type) {
		case string: // string 타입인가?

			data_len_byte, err1 := util.UInt32_to_Bytes(uint32(len(v)))
			if err1 != nil {
				return nil, err1
			} else {
				return_byte_buffer.Write(data_len_byte) // 문자열 길이 -> 리틀 엔디언 바이트 변환
				return_byte_buffer.WriteString(v)
			}
			// 문자열 -> 바이트 변환
		case uint32: // 부호 없는 정수 타입인가?

			data_len_byte, err2 := util.UInt32_to_Bytes(uint32(4)) // uint32 이므로 4바이트
			if err2 != nil {
				return nil, err2
			} else {
				return_byte_buffer.Write(data_len_byte)
			}

			data, err3 := util.UInt32_to_Bytes(v) // uint32 리틀 엔디언 바이트
			if err3 != nil {
				return nil, err3
			} else {
				return_byte_buffer.Write(data)
			}

		default:
			return nil, fmt.Errorf("지원하지 않은 데이터 타입입니다. uint32 및 string만 '직렬화' 지원됩니다.") // 지원하지 않은 경우 바로 예외 발생
		}

	}

	// [3/3]"_END" 삽입
	return_byte_buffer.Write([]byte("_END"))

	return return_byte_buffer.Bytes(), nil
}

// 역직렬화 ( 하나의 바이트 --> 구조화된 데이터 )
func To_Deserialization(data []byte) ([]Deserialization_struct, error) {

	output2 := make([]Deserialization_struct, 0)

	output := Deserialization_struct{
		Command:  enums.Agent_enum(0),
		Dyn_data: make([]interface{}, 0),
	}

	command, err1 := util.Bytes_to_Int32(data[0:4]) // 리틀 엔디언 바이트 -> 32정수 변환
	if err1 != nil {
		return []Deserialization_struct{}, err1
	} else {
		output.Command = enums.Agent_enum(command)
	}

	current_index := uint32(4)
	last_index := uint32(8)
	finish_index := uint32(len(data))
	for last_index <= finish_index {
		if bytes.Equal(data[current_index:last_index], []byte("_END")) {
			output2 = append(output2, output)
			output = Deserialization_struct{
				Command:  enums.Agent_enum(0),
				Dyn_data: make([]interface{}, 0),
			}

			// 파싱 최종인가?
			if last_index == finish_index {
				break
			} else {
				// 아직 파싱이 더 남은 경우, ( 2차원 )

				// 명령어 미리 추출
				current_index = last_index
				last_index += 4
				output.Command = enums.Agent_enum(util.ERROR_PROCESSING(util.Bytes_to_Int32(data[current_index:last_index]))) // bytes(리틀엔디언) -> 정수 -> enums.Agent_enum 변환

				// 다음 동적 데이터로 인덱스 이동
				current_index = last_index
				last_index += 4

				continue
			}

		} else {

			dyn_data_length, err2 := util.Bytes_to_UInt32(data[current_index:last_index]) // 리틀 엔디언 바이트 -> 32정수 변환
			if err2 != nil {
				return []Deserialization_struct{}, err2
			} else {
				// 동적 데이터 앞부분으로 인덱스 이동
				current_index = last_index
				last_index += dyn_data_length
				//fmt.Printf("최근 command %v\n", output.Command)

				dyn_data := data[current_index:last_index]
				copied_dyn_data := make([]byte, len(dyn_data))
				copy(copied_dyn_data, dyn_data)

				output.Dyn_data = append(output.Dyn_data, copied_dyn_data) // 동적 데이터 삽입

				current_index = last_index
				last_index += uint32(4)
				continue

			}

		}
	}

	return output2, nil
}

func isASCII(data []byte) bool {
	for _, b := range data {
		if b > 0x7F {
			return false
		}
	}
	return true
}
