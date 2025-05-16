package sql

import (
	"fmt"
	"strings"
	"sync"

	_ "github.com/go-sql-driver/mysql"
)

type DB_Manager struct {
	DB     *Mysql
	mutex_ *sync.Mutex
}

func New_DB_Manager(serverIP string, port int, dbUser string, dbPassword string, dbname string) *DB_Manager {

	MySQL_obj := New_Mysql(serverIP, port, dbUser, dbPassword, dbname)
	if MySQL_obj == nil {
		panic("DB 초기화 실패")
	}

	// 구조체 생성
	core_control_db := DB_Manager{
		DB:     MySQL_obj,
		mutex_: &sync.Mutex{},
	}

	// DB 초기화
	core_control_db.Init()

	return &core_control_db

}

func (as *DB_Manager) Init() {
	// 'file_save' 테이블 체크 --> 없으면 생성
	file_save_table_create_query := `
	CREATE TABLE IF NOT EXISTS file_save (
		agent_id VARCHAR(128) NOT NULL,
		saved_file_path VARCHAR(256) NOT NULL,
		file_path_on_endpoint VARCHAR(255) NOT NULL,
		file_size BIGINT NOT NULL,
		sha256 VARCHAR(64) NOT NULL
	);`

	if err := as.DB.Exec(file_save_table_create_query); err != nil {
		fmt.Print("안돼")
		fmt.Printf("file_save 테이블 생성 실패 -> %s, %v \n", file_save_table_create_query, err)
	}

}

// 바이너리 파일 확인 및 저장
// 바이너리 존재 여부 체크
func (as *DB_Manager) Check_exists_Binary_File(agent_id string, file_path_on_endpoint string, file_size uint32) bool {
	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	cmd := fmt.Sprintf("SELECT * FROM file_save WHERE agent_id = '%s' AND file_path_on_endpoint = '%s' AND file_size = '%d'", agent_id, strings.ReplaceAll(file_path_on_endpoint, "\\", "\\\\"), file_size)
	if result, err := as.DB.Query(cmd); err == nil {
		if len(result) > 0 {
			return true
		} else {

			// 실제로는 파일이 있는 지확인
			cmd = fmt.Sprintf("SELECT * FROM file_save WHERE file_path_on_endpoint = '%s' AND file_size = '%d'", file_path_on_endpoint, file_size)
			if result, err := as.DB.Query(cmd); err == nil {
				if len(result) > 0 {
					// agent_id와 매핑하는 row 생성
					cmd = fmt.Sprintf("INSERT INTO file_save(agent_id, file_path_on_endpoint, saved_file_path, file_size, sha256) VALUES( '%s', '%s', '%s', '%d', '%s')", agent_id, strings.ReplaceAll(file_path_on_endpoint, "\\", "\\\\"), result[0]["saved_file_path"], file_size, result[0]["sha256"])
					as.DB.Exec(cmd)
					return true
				} else {
					return false
				}
			}

			return false
		}
	} else {
		return false
	}
}

// 바이너리 저장
func (as *DB_Manager) Insert_Binary_File(agent_id string, file_path_on_endpoint string, saved_file_path string, file_size uint32, sha256 string) error {
	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	cmd := fmt.Sprintf("INSERT INTO file_save(agent_id ,file_path_on_endpoint, saved_file_path, file_size, sha256) VALUES('%s', '%s', '%s', '%d', '%s')", agent_id, strings.ReplaceAll(file_path_on_endpoint, "\\", "\\\\"), strings.ReplaceAll(saved_file_path, "\\", "\\\\"), file_size, sha256)
	return as.DB.Exec(cmd)
}

/*
	[OUTPUT]
*/
// 1. 다른 서버에서 엔드포인트 파일 요청한 경우
func (as *DB_Manager) Output_Binary_File_Path_from_CoreServer(agent_id string, file_path_on_endpoint string) string {
	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	cmd := fmt.Sprintf("SELECT * FROM file_save WHERE agent_id = '%s' AND file_path_on_endpoint = '%s'", agent_id, strings.ReplaceAll(file_path_on_endpoint, "\\", "\\\\"))
	if result, err := as.DB.Query(cmd); err == nil {
		if len(result) > 0 {
			return strings.ReplaceAll(result[0]["saved_file_path"].(string), "\\\\", "\\") //  실제 CoreServer에 저장된 파일 경로를 반환
		} else {
			return ""
		}
	}
	return ""
}

// 2. sha256 가져오기
func (as *DB_Manager) Output_Binary_File_SHA256_from_CoreServer(agent_id string, file_path_on_endpoint string, file_size uint32) string {
	as.mutex_.Lock()
	defer as.mutex_.Unlock()

	cmd := fmt.Sprintf("SELECT sha256 FROM file_save WHERE agent_id = '%s' AND file_path_on_endpoint = '%s' AND file_size = '%d'", agent_id, strings.ReplaceAll(file_path_on_endpoint, "\\", "\\\\"), file_size)
	if result, err := as.DB.Query(cmd); err == nil {
		if len(result) > 0 {
			return result[0]["sha256"].(string)
		} else {
			return ""
		}
	}
	return ""
}

/*
에이전트 정보
// 1. 에이전트 정보 등록하기
func (as *DB_Manager) InsertAgent_2_DB(agent_id string, os_info string, agent_source_ip string) error {
	cmd := fmt.Sprintf("INSERT INTO agent(AGENT_ID, OS, SOURCE_IP, LAST_CHECK_TIME) VALUES('%s', '%s', '%s', '%s')", agent_id, os_info, agent_source_ip, util.ERROR_PROCESSING(util.Getglobaltime()))
	return as.Coreserver_DB.Exec(cmd)
}

// 2. 에이전트 정보 조회하기
func (as *DB_Manager) QueryAgent_2_DB(agent_id string) ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM agent WHERE AGENT_ID = '%s'", agent_id)
	return as.Coreserver_DB.Query(cmd)
}

// 모든 [에이전트] 데이터 내보내기
func (as *DB_Manager) Query_ALL_Agent_2_DB() ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM agent ")
	return as.Coreserver_DB.Query(cmd)
}

/* 프로세스 인스턴스 정보
// 3. 프로세스 인스턴스 정보 등록하기 ( JSON )
func (as *DB_Manager) InsertProcessInstance_2_DB(agent_id string, process_instance_id string, process_instance_map map[string]interface{}) error {

	// JSON 문자열 만들기
	json_byte, err := json.Marshal(process_instance_map)
	if err != nil {
		return err
	}

	cmd := fmt.Sprintf("INSERT INTO process_instance(INSTANCE_ID, AGENT_ID_FK, JSON) VALUES('%s', '%s', '%s')", process_instance_id, agent_id, string(json_byte))
	return as.Coreserver_DB.Exec(cmd)
}

// 4. 프로세스 인스턴스 정보 조회하기 ( JSON )
func (as *DB_Manager) QueryProcessInstance_2_DB(agent_id string, process_instance_id string) ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM process_instance WHERE AGENT_ID_FK = '%s' AND INSTANCE_ID = '%s'", agent_id, process_instance_id)
	return as.Coreserver_DB.Query(cmd)
}

// 모든 [프로세스 인스턴스] 데이터 내보내기
func (as *DB_Manager) Query_ALL_ProcessInstance_2_DB() ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM process_instance ")
	return as.Coreserver_DB.Query(cmd)
}

/* 차단 정보
// 5. 에이전트 차단 정보 등록하기
func (as *DB_Manager) InsertResponseFile_2_DB(agent_id string, sha256 string, is_process bool) error {

	types := "FILE"
	if is_process {
		types = "PROCESS"
	}

	// 중복 검사
	test := fmt.Sprintf("SELECT * FROM response WHERE AGENT_ID_FK = '%s' AND TYPE = '%s' AND SHA256 = '%s'", agent_id, types, sha256)
	rows, err := as.Coreserver_DB.Query(test)
	if err != nil || len(rows) > 0 {
		return nil
	}

	cmd := fmt.Sprintf("INSERT INTO response( AGENT_ID_FK, TYPE, REMOTEIP,SHA256) VALUES('%s', '%s', NULL, '%s')", agent_id, "FILE", sha256)
	return as.Coreserver_DB.Exec(cmd)
}
func (as *DB_Manager) InsertResponseIP_2_DB(agent_id string, remoteip string) error {
	// 중복 검사
	test := fmt.Sprintf("SELECT * FROM response WHERE AGENT_ID_FK = '%s' AND TYPE = 'NETWORK' AND REMOTEIP = '%s'", agent_id, remoteip)
	rows, err := as.Coreserver_DB.Query(test)
	if err != nil || len(rows) > 0 {
		return nil
	}

	cmd := fmt.Sprintf("INSERT INTO response( AGENT_ID_FK, TYPE, REMOTEIP,SHA256) VALUES('%s', '%s', '%s', NULL)", agent_id, "NETWORK", remoteip)
	return as.Coreserver_DB.Exec(cmd)
}

// 6. 에이전트 차단 정보 조회하기
func (as *DB_Manager) QueryResponse_2_DB(agent_id string) ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM response WHERE AGENT_ID_FK = '%s'", agent_id)
	return as.Coreserver_DB.Query(cmd)
}
func (as *DB_Manager) Query_ALL_Response_2_DB() ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM response")
	return as.Coreserver_DB.Query(cmd)
}

// 7. 에이전트 차단 정보 삭제하기
func (as *DB_Manager) DeleteResponseFile_2_DB(agent_id string, sha256 string) error {
	cmd := fmt.Sprintf("DELETE FROM response WHERE AGENT_ID_FK = '%s' AND TYPE = 'FILE' AND SHA256 = '%s'", agent_id, sha256)
	return as.Coreserver_DB.Exec(cmd)
}
func (as *DB_Manager) DeleteResponseIP_2_DB(agent_id string, remoteip string) error {
	cmd := fmt.Sprintf("DELETE FROM response WHERE AGENT_ID_FK = '%s' AND TYPE = 'NETWORK' AND REMOTEIP = '%s'", agent_id, remoteip)
	return as.Coreserver_DB.Exec(cmd)
}

/* 이상탐지 시
// 1. 이상탐지 시 정보 등록하기
func (as *DB_Manager) InsertAnomaly_2_DB(agent_id string, process_sha256 string, file_size uint32, anomaly_score int, anomaly_threshold int, llm_report string, llm_summary string, llm_tags string, timestamp string) error {

	cmd := fmt.Sprintf("INSERT INTO anomaly( AGENT_ID_FK, PROCESS_SHA256, FILE_SIZE, ANOMALY_SCORE, ANOMALY_THRESHOLD, LLM_REPORT, LLM_SUMMARY, LLM_TAGS, TIMESTAMP) VALUES('%s', '%s', '%d', '%d', '%d', '%s', '%s', '%s', '%s')", agent_id, process_sha256, file_size, anomaly_score, anomaly_threshold, llm_report, llm_summary, llm_tags, timestamp)
	return as.Coreserver_DB.Exec(cmd)
}

// 2. 이상탐지 모든 정보 조회하기
func (as *DB_Manager) Query_ALL_Anomaly_2_DB() ([]map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM anomaly")
	return as.Coreserver_DB.Query(cmd)
}

/* 정책
// 1. 정책 정보 가져오기

// 유형 평가 가져오기
func (as *DB_Manager) Query_LLM_Type_Eval_Policy_2_DB() (map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM llm_type_eval")
	if result, err := as.Policy_DB.Query(cmd); err == nil {
		return result[0], nil
	} else {
		return nil, err
	}
}

// 중간 평가 가져오기
func (as *DB_Manager) Query_LLM_Middle_Eval_Policy_2_DB() (map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM llm_middle_eval")
	if result, err := as.Policy_DB.Query(cmd); err == nil {
		return result[0], nil
	} else {
		return nil, err
	}
}

// 최종 평가 가져오기
func (as *DB_Manager) Query_Response_Policy_2_DB() (map[string]interface{}, error) {
	cmd := fmt.Sprintf("SELECT * FROM response")
	if result, err := as.Policy_DB.Query(cmd); err == nil {
		return result[0], nil
	} else {
		return nil, err
	}
}
*/
