package RegisteredServer

import (
	"CoreServer/Socket"
	"CoreServer/util"
	"fmt"
	"net"
	"sync"
)

type RegisterServer_Manager struct {
	registered_server_info map[string]*registerServer
	mutex_                 *sync.Mutex
}

func New_RegisterServer_Manager() *RegisterServer_Manager {
	return &RegisterServer_Manager{
		registered_server_info: make(map[string]*registerServer, 0),
		mutex_:                 &sync.Mutex{},
	}
}

// 서버 등록
func (as *RegisterServer_Manager) Append_Server(server_nickname string, server_ip string, server_port uint32) bool {

	//as.mutex_.Lock()
	//defer as.mutex_.Unlock()
	//as.registered_server_info[server_nickname] = new_Register_Server(server_nickname, enum_strings, server_ip, server_port)
	//return true

	if as.Nothing_key_Server(server_nickname) {

		as.registered_server_info[server_nickname] = new_Register_Server(server_nickname, server_ip, server_port)

		return true
	} else {
		return false
	}

}

// 등록된 서버에 TCP 통신 ( nickname -> 조회 -> RegisterServer 객체 습득 후 TCP 전달)
// BroadCast
/*
func (as *RegisterServer_Manager) Send_2_ALL_Server_with_mapped(input_enum enums.Agent_enum, event_data map[string]interface{}) {

	output, _ := util.Map_to_JSON(event_data)

	// enum -> string
	enum_string, _ := input_enum.String()

	// Object를 구하고, Object의 멤버에서 등록된 enums 문자열이 포함된 경우 이벤트 전달
	for server_nickname, object := range as.registered_server_info {
		for _, EnumString := range object.enum_strings {
			if enum_string == EnumString {
				if !object.send(output) {
					as.Remove_Server(server_nickname)
				}
			}
		}
	}
	//time.Sleep(time.Second * 2)

}*/
func (as *RegisterServer_Manager) Send_list_map(event_data []map[string]interface{}) {

	if len(event_data) == 0 {
		return
	}

	output, _ := util.Map_to_JSON(event_data)

	// Object를 구하고, Object의 멤버에서 등록된 enums 문자열이 포함된 경우 이벤트 전달
	for server_nickname, object := range as.registered_server_info {
		if !object.send(output) {
			as.Remove_Server(server_nickname)
		}
		fmt.Print("등록된 서버 전달 완료")
	}
}

// 등록된 서버 제거
func (as *RegisterServer_Manager) Remove_Server(server_nickname string) bool {

	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	if !as.Nothing_key_Server(server_nickname) {

		new := map[string]*registerServer{}
		for key, value := range as.registered_server_info {
			if server_nickname != key {
				new[key] = value
			}
		}

		as.registered_server_info = new
		return true
	} else {
		return false
	}
}

// 서버 등록 체킹
func (as *RegisterServer_Manager) Nothing_key_Server(server_nickname string) bool {
	if _, ok := as.registered_server_info[server_nickname]; !ok {
		return true
	} else {
		return false
	}
}

/*
=============================================================================================

=============================================================================================

=============================================================================================
*/
type registerServer struct {
	server_nickname        string
	server_connection_info *Socket.Agent_Socket
	mutex                  *sync.Mutex
}

func new_Register_Server(server_nickname string, server_ip string, server_port uint32) *registerServer {

	// 1. TCP 소켓 연결 ( 클라이언트 )
	TCPconn, err := net.Dial("tcp", fmt.Sprintf("%s:%d", server_ip, server_port))
	if err != nil { // 예외 처리
		panic(err)
	}

	return &registerServer{
		server_nickname:        server_nickname,
		server_connection_info: Socket.New_Agent_Socket(TCPconn),
		mutex:                  &sync.Mutex{},
	}
}

func (as *registerServer) send(event_data string) bool {
	as.mutex.Lock()
	defer as.mutex.Unlock()

	if err2 := as.server_connection_info.Send([]byte(event_data)); err2 == nil {
		return true
	} else {
		return false
	}
}
