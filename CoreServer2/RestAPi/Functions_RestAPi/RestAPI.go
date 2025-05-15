package Functions_RestAPi

import (
	ShareObject "CoreServer/Share_Object"
	"CoreServer/util"
	"fmt"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
)

// RestAPI 서버 메인 구조체
type RestAPI_struct struct {
	Router      *gin.Engine
	server_port uint32
	shareobject *ShareObject.Sharing
}

func New_RestAPI(server_port uint32, shareobject *ShareObject.Sharing) *RestAPI_struct {
	return &RestAPI_struct{
		Router:      gin.Default(),
		server_port: server_port,
		shareobject: shareobject,
	}
}

// 경로 설정
func (as *RestAPI_struct) SetupRoute() {

	as.Router.GET("/ping", as.ping) // TEST
	/* CoreServer -> 솔루션 서버 */

	// 1. 외부 솔루션 서버 등록
	as.Router.POST("/server_register", as.server_register)

	/* 솔루션 서버 -> CoreServer */

	// 1. 파일 바이너리 요청
	as.Router.GET("/request/file", as.request_file) // 파라미터 agent_id, file_path, file_size

	// 2. 차단 ( 프로세스파일 , 일반파일, 원격지 네트워크 차단 )
	as.Router.GET("/request/response/process", as.response_process)
	as.Router.GET("/request/response/file", as.response_file)
	as.Router.GET("/request/response/network", as.response_network)

	// -- 아래부터는 조회
	as.Router.GET("/request/view/agents", as.request_view_agents) // 에이전트 상태 반환
}

// //////////////////////////////////////////////////////////////////////////////////////////////////
// //////////////////////////////////// RESTAPI  함수 로직 모음 //////////////////////////////////////
// //////////////////////////////////////////////////////////////////////////////////////////////////

// 1. 외부 솔루션 서버 등록
func (as *RestAPI_struct) server_register(c *gin.Context) {

	// JSON요청 받기
	JSON := http_request_2_map(c)
	if JSON == nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"message": "Bad Request",
		})
	}
	/*
		{
			"server_nickname": "",
			"server_ip": "",
			"server_port": (float64)
			"enums": [] []string
		}
	*/

	// 변수 추출
	server_nickname := JSON["server_nickname"].(string)
	server_ip := JSON["server_ip"].(string)
	server_port := util.Float64_to_uint32(JSON["server_port"].(float64))
	// 로직

	// 1. 등록된 서버 관리자에 "솔루션 서버"추가
	as.shareobject.RegisteredServer_Manager.Append_Server(
		server_nickname,
		server_ip,
		server_port,
	)

	// 반환
	c.JSON(http.StatusOK, gin.H{
		"message": "success",
	})
}

// ///////////////////////////////////////////////
// response 차단
// 1. process
func (as *RestAPI_struct) response_process(c *gin.Context) {
	if len(c.Query("agent_id")) == 0 || len(c.Query("sha256")) == 0 || len(c.Query("filesize")) == 0 || len(c.Query("is_remove")) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"message": "Bad Request",
		})
		return
	}

	agent_id := c.Query("agent_id")                                                           // 에이전트 특정
	sha256 := c.Query("sha256")                                                               // 검증용
	filesize := uint32(util.ERROR_PROCESSING(strconv.ParseUint(c.Query("filesize"), 10, 32))) // 파일 크기
	is_remove := bool(util.ERROR_PROCESSING(strconv.ParseBool(c.Query("is_remove"))))         // 삭제 여부

	AGENT_Controller := as.shareobject.Output_Agent_Controller_with_ID(
		agent_id,
	)
	if AGENT_Controller == nil {
		c.JSON(http.StatusOK, gin.H{
			"message": "에이전트 ID가 없습니다.",
		})
		return
	}

	result := AGENT_Controller.Process_Response(
		sha256,
		filesize,
		is_remove,
	)

	c.JSON(http.StatusOK, gin.H{
		"message": result,
	})

}

// 2. file
func (as *RestAPI_struct) response_file(c *gin.Context) {
	if len(c.Query("agent_id")) == 0 || len(c.Query("sha256")) == 0 || len(c.Query("filesize")) == 0 || len(c.Query("is_remove")) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"message": "Bad Request",
		})
		return
	}

	agent_id := c.Query("agent_id")                                                           // 에이전트 특정
	sha256 := c.Query("sha256")                                                               // 검증용
	filesize := uint32(util.ERROR_PROCESSING(strconv.ParseUint(c.Query("filesize"), 10, 32))) // 파일 크기
	is_remove := bool(util.ERROR_PROCESSING(strconv.ParseBool(c.Query("is_remove"))))         // 삭제 여부                                           // 삭제 여부

	AGENT_Controller := as.shareobject.Output_Agent_Controller_with_ID(
		agent_id,
	)
	if AGENT_Controller == nil {
		c.JSON(http.StatusOK, gin.H{
			"message": "에이전트 ID가 없습니다.",
		})
		return
	}

	result := AGENT_Controller.File_Response(
		sha256,
		filesize,
		is_remove,
	)

	c.JSON(http.StatusOK, gin.H{
		"message": result,
	})
}

// 3. network
func (as *RestAPI_struct) response_network(c *gin.Context) {
	if len(c.Query("agent_id")) == 0 || len(c.Query("remote_ip")) == 0 || len(c.Query("is_remove")) == 0 {
		c.JSON(http.StatusOK, gin.H{
			"message": "Bad Request",
		})
		return
	}

	agent_id := c.Query("agent_id")                                                   // 에이전트 특정
	remote_ip := c.Query("remote_ip")                                                 // 원격 IP
	is_remove := bool(util.ERROR_PROCESSING(strconv.ParseBool(c.Query("is_remove")))) // 삭제 여부

	AGENT_Controller := as.shareobject.Output_Agent_Controller_with_ID(
		agent_id,
	)
	if AGENT_Controller == nil {
		c.JSON(http.StatusOK, gin.H{
			"message": "에이전트 ID가 없습니다.",
		})
		return
	}

	result := AGENT_Controller.Network_Response(
		remote_ip,
		is_remove,
	)

	c.JSON(http.StatusOK, gin.H{
		"message": result,
	})

}

// ///////////////////////////////////////////////////////////////////////////////////////////
// 1. 파일 바이너리 요청

func (as *RestAPI_struct) request_file(c *gin.Context) {
	agent_id := c.Query("agent_id") // 에이전트 특정
	//sha256 := c.Query("sha256")       // 검증용
	file_path := c.Query("file_path") // 파일 타겟

	// mysql에서 먼저 있는지 존재체크
	saved_file_path := as.shareobject.Database.Output_Binary_File_Path_from_CoreServer(agent_id, file_path)
	if saved_file_path != "" {

		file_bin, _ := as.shareobject.FileIo.Read_File(saved_file_path)

		base64 := util.Bytes_to_Base64(file_bin)

		c.JSON(http.StatusOK, gin.H{
			"output":  base64,
			"message": "success",
		})
		return
	}

	// 컨트롤러 반환
	Agent_Controller := as.shareobject.Output_Agent_Controller_with_ID(
		agent_id,
	)

	// 요청
	_, base64, err := Agent_Controller.Request_Real_File(
		file_path,
	)

	output := base64
	if err != nil {
		output = fmt.Sprintf("%v", err) // 에러 값 반환
	}

	// 반환
	c.JSON(http.StatusOK, gin.H{
		"output":  output,
		"message": "success",
	})
}

// TEST
func (as *RestAPI_struct) ping(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"message": "pong",
	})
}

// UTIL

// 1. http 요청을 map으로 변환
// 정수는 float64로 변환되어 나오므로,, math.Trunc을 사용하고 uint32등으로 변환조치하라.
func http_request_2_map(c *gin.Context) map[string]interface{} {
	input_data := make(map[string]interface{})
	if err := c.ShouldBindJSON(&input_data); err != nil { // 입력 데이터 받아오기

		return nil
	}
	return input_data
}

// view
// 1. 에이전트 상태 반환
func (as *RestAPI_struct) request_view_agents(c *gin.Context) {

	agent_status := as.shareobject.Output_Agent_Controller()

	output := util.ERROR_PROCESSING(util.Map_to_JSON(agent_status))

	// 반환
	/*
		{
			Output_Agent_Controller 참조
		}
	*/
	c.JSON(http.StatusOK, gin.H{
		"output": output,
	})
}
