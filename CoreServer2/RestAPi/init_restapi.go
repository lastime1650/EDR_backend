package RestAPi

import (
	"CoreServer/RestAPi/Functions_RestAPi"
	ShareObject "CoreServer/Share_Object"
	"fmt"
)

/*
<< 무슨 일을 하는 가? >>
1. RestAPI 서버를 운영 및 관리한다.
2. 현 서버에 기록된 모든 에이전트를 관리 및 정보를 확인할 수 있다.
3. 에이전트 Control이 가능하다.
*/

// init
func Start_RestAPI_Server(server_ip string, server_port uint32, share_object *ShareObject.Sharing) error {

	// RestAPI 서버 구조체 생성
	web_inst := Functions_RestAPi.New_RestAPI(server_port, share_object)

	// 경로 설정
	web_inst.SetupRoute()

	// restapi 시작
	server_port_2_string := fmt.Sprintf("%s:%d", server_ip, server_port) // 서버 포트 -> str
	return web_inst.Router.Run(server_port_2_string)                     // 서버 시작
}
