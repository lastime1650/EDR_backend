package analysisserver

import (
	"CoreServer/util"
	"fmt"
	"net/url"
)

type Analysis_request_enum string

const (
	FileType    Analysis_request_enum = "file"
	NetworkType Analysis_request_enum = "network"
	//registry Analysis_request_enum = "registry"
)

type AnalysisServer_Manager struct {
	server_ip   string
	server_port uint32
}

func New_AnalysisServer_Manager(server_ip string, server_port uint32) *AnalysisServer_Manager {
	return &AnalysisServer_Manager{
		server_ip:   server_ip,
		server_port: server_port,
	}
}

type Request_Analysis_Data struct {
	// file
	Base64Bin string // base64
	FileSize  uint32 //
	Sha256    string

	// network
	Remote_ip string
}

type Request_Analysis_struct struct {
	SCRIPT_TYPE Analysis_request_enum
	DATA        Request_Analysis_Data
}

// 데이터 분석 요청
func (as *AnalysisServer_Manager) Request_Analysis(Data Request_Analysis_struct) {

	req_json := map[string]interface{}{
		"SCRIPT_TYPE": string(Data.SCRIPT_TYPE),
		"DATA": map[string]interface{}{
			"binary":    Data.DATA.Base64Bin,
			"file_size": Data.DATA.FileSize,
			"sha256":    Data.DATA.Sha256,
			"remote_ip": Data.DATA.Remote_ip,
		},
	}
	req_json_bytes := []byte(util.ERROR_PROCESSING(util.Map_to_JSON(req_json)))

	req_url := fmt.Sprintf("http://%s:%d/API/Analysis_Request", as.server_ip, as.server_port)

	util.RestAPI_POST(req_url, &req_json_bytes) // 별다른 예외처리 없음 (비동기 처리이므로 실패의 경우 다시 요청할 수 있음)

}

// sha256넘겨 분석되었는 지 확인
func (as *AnalysisServer_Manager) Check_Analysis_Result_SHA256(sha256 string) bool {

	//fmt.Print("sha256넘겨 분석되었는 지 확인")

	req_url := fmt.Sprintf("http://%s:%d/API/Check_Analysis_Result", as.server_ip, as.server_port)

	req_json := map[string]interface{}{
		"SCRIPT_TYPE": string(FileType),
		"DATA": map[string]interface{}{
			"sha256": sha256,
		},
	}

	Parm := url.Values{}

	Parm.Add("input_JSON", util.ERROR_PROCESSING(util.Map_to_JSON(req_json)))

	if output, err := util.RestAPI_GET(req_url, &Parm); err == nil {

		if output_map, err := util.JSON_to_Map(output); err == nil {

			//fmt.Print(output_map)

			return output_map["result"].(bool)

		}

		return false
	}

	return false
}

// remote_ip넘겨 분석되었는 지 확인
func (as *AnalysisServer_Manager) Check_Analysis_Result_remote_ip(remote_ip string) bool {

	//fmt.Print("sha256넘겨 분석되었는 지 확인")

	req_url := fmt.Sprintf("http://%s:%d/API/Check_Analysis_Result", as.server_ip, as.server_port)

	req_json := map[string]interface{}{
		"SCRIPT_TYPE": string(NetworkType),
		"DATA": map[string]interface{}{
			"remote_ip": remote_ip,
		},
	}

	Parm := url.Values{}

	Parm.Add("input_JSON", util.ERROR_PROCESSING(util.Map_to_JSON(req_json)))

	if output, err := util.RestAPI_GET(req_url, &Parm); err == nil {

		if output_map, err := util.JSON_to_Map(output); err == nil {

			//fmt.Print(output_map)

			return output_map["result"].(bool)

		}

		return false
	}

	return false
}
