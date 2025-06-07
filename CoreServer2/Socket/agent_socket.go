package Socket

import (
	"CoreServer/parse"
	"CoreServer/util"
	"fmt"
	"net"
	"sync"
)

type Agent_Socket struct {
	TCPconn net.Conn
	Mutex   sync.Mutex

	Is_Disconnected_Mutex sync.Mutex
	Is_Disconnected       bool
}

func New_Agent_Socket(TCPconn net.Conn) *Agent_Socket {
	return &Agent_Socket{
		TCPconn: TCPconn,
		Mutex:   sync.Mutex{},

		Is_Disconnected_Mutex: sync.Mutex{},
		Is_Disconnected:       false,
	}
}

func (as *Agent_Socket) Send(data []byte) error {
	// 길이 값을 리틀 엔디언으로 변환
	data_length, err1 := util.UInt32_to_Bytes(uint32(len(data)))
	if err1 != nil {
		return err1
	}

	// [1/2] 전송 데이터 길이 전송
	_, err2 := as.TCPconn.Write(data_length)
	if err2 != nil {
		return err2
	}

	// [2/2] 전송 데이터 전송
	_, err3 := as.TCPconn.Write(data)
	if err3 != nil {
		return err3
	}

	return nil
}

func (as *Agent_Socket) Receive() ([]byte, error) {

	// [1/2]데이터 수신 준비
	len_data_recv_buffer := make([]byte, 4)
	_, err1 := as.TCPconn.Read(len_data_recv_buffer) // 4바이트 수신 ( 이는 데이터 길이 (little))
	if err1 != nil {
		return nil, err1
	}
	data_recv_buffer_length, err2 := util.Bytes_to_UInt32(len_data_recv_buffer) // 에이전트가 전송할 총 길이 -> 정수 변환
	if err2 != nil {
		return nil, err2
	}

	// [2/2]실제 데이터 수신 ( 받을 때까지 반복 수신처리 )
	data_recv_buffer := make([]byte, data_recv_buffer_length)

	currnet_data_recv_buffer_length := uint32(0)
	for currnet_data_recv_buffer_length < data_recv_buffer_length {

		len, err2 := as.TCPconn.Read(data_recv_buffer[currnet_data_recv_buffer_length:]) // 데이터 수신
		if err2 != nil {
			return nil, err2
		}
		currnet_data_recv_buffer_length += uint32(len)

	}

	return data_recv_buffer, nil
}

func (as *Agent_Socket) Disconnect() error {

	as.Is_Disconnected_Mutex.Lock()
	defer as.Is_Disconnected_Mutex.Unlock()

	if as.Is_Disconnected {
		return nil
	} else {
		as.Is_Disconnected = true
		return as.TCPconn.Close()
	}
}

func (as *Agent_Socket) Check_Disconnected() bool {
	as.Is_Disconnected_Mutex.Lock()
	defer as.Is_Disconnected_Mutex.Unlock()

	return as.Is_Disconnected
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

// 에이전트에게 명령
func (as *Agent_Socket) Send_Agent_Command(input_data *parse.Deserialization_struct) ([]parse.Deserialization_struct, error) {

	if serialized_data, err := parse.To_Serialization(*input_data); err == nil {

		as.Mutex.Lock()         // 점유
		defer as.Mutex.Unlock() // 리턴시 해제예약

		// 에이전트에게 TCP 요청
		if as.Send(serialized_data) != nil {
			as.Disconnect()
			return nil, fmt.Errorf("에이전트에게 데이터를 전송하지 못했습니다. <<연결을 끊겠습니다.>>")
		} else {

			// 3. 에이전트가 전송한 데이터 수신
			recv_data, err2 := as.Receive()
			if err2 != nil {
				as.Disconnect()
				return nil, fmt.Errorf("에이전트에게 데이터를 전송하지 못했습니다. <<연결을 끊겠습니다.>>")
			} else {
				/*
					역직렬화 수행
				*/
				if recv_data_parse, err3 := parse.To_Deserialization(recv_data); err3 != nil {
					return nil, fmt.Errorf("에이전트가 전송한 데이터 '역 직렬화' 완수하지 못했습니다. <<연결을 끊겠습니다.>>")

				} else {
					// 최종성공
					return recv_data_parse, nil
				}
			}
		}

	} else {
		return nil, fmt.Errorf("에이전트에게 전송할 데이터가 옳지 않습니다.")
	}

}
