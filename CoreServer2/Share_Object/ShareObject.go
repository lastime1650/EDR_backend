package ShareObject

import (
	analysisserver "CoreServer/AnalysisServer"
	"CoreServer/RegisteredServer"
	siem "CoreServer/SIEM"
	agent_manager "CoreServer/agent_management"
	"CoreServer/sql"
	"CoreServer/util"
	"sync"
)

type Sharing struct {
	RegisteredServer_Manager *RegisteredServer.RegisterServer_Manager
	Agents                   []*agent_manager.Agent_Controller
	agents_mutex             *sync.Mutex

	Database *sql.DB_Manager
	FileIo   *util.File_io

	AnalysisServer_Manager *analysisserver.AnalysisServer_Manager

	ElasticSearch_Manager *siem.ElasticSearchManager
	Kafka_Manager         *siem.KafkaManager
}

func New_Share_Object(

	DB_HOST string,
	DB_PORT int,
	DB_USER string,
	DB_PASS string,

	ELASTICSEARCH_HOST string,
	ELASTICSEARCH_PORT int,

	KAFKA_HOST string,
	KAFKA_PORT int,

	ANALYSIS_SERVER_HOST string,
	ANALYSIS_SERVER_PORT uint32,

	LOCAL_STORAGE_DIR string,

) *Sharing {

	return &Sharing{
		RegisteredServer_Manager: RegisteredServer.New_RegisterServer_Manager(),

		Agents:       []*agent_manager.Agent_Controller{},
		agents_mutex: &sync.Mutex{},
		/*
			Database:               sql.New_DB_Manager("192.168.0.1", 3306, "root", "1234", "share"),
			FileIo:                 util.New_File_io("E:\\save_file\\"),
			AnalysisServer_Manager: analysisserver.New_AnalysisServer_Manager("192.168.0.1", 6060),
			//
			ElasticSearch_Manager: siem.New_ElasticSearchManager("192.168.0.1", 9200),
			Kafka_Manager:         siem.New_KafkaManager("siem-edr-processbehavior-event", "192.168.0.1", 29092, 1, 1),
		*/
		Database:               sql.New_DB_Manager(DB_HOST, DB_PORT, DB_USER, DB_PASS, "share"),
		FileIo:                 util.New_File_io(LOCAL_STORAGE_DIR),
		AnalysisServer_Manager: analysisserver.New_AnalysisServer_Manager(ANALYSIS_SERVER_HOST, ANALYSIS_SERVER_PORT),
		//
		ElasticSearch_Manager: siem.New_ElasticSearchManager(ELASTICSEARCH_HOST, ELASTICSEARCH_PORT),
		Kafka_Manager:         siem.New_KafkaManager("siem-edr-processbehavior-event", KAFKA_HOST, KAFKA_PORT, 1, 1),
	}

}

func (as *Sharing) Append_Agent_Controller(Controller *agent_manager.Agent_Controller) bool {

	as.agents_mutex.Lock()
	defer as.agents_mutex.Unlock()

	for _, value := range as.Agents {
		if value.Output_AGENT_ID() == Controller.Output_AGENT_ID() { // 중복시 추가 안함
			return false
		}
	}

	as.Agents = append(as.Agents, Controller)

	return true

}

func (as *Sharing) Remove_Agent_Controller(Controller *agent_manager.Agent_Controller) bool {

	as.agents_mutex.Lock()
	defer as.agents_mutex.Unlock()

	remove_check := false

	tmp_ := []*agent_manager.Agent_Controller{}

	for _, value := range as.Agents {
		if value.Output_AGENT_ID() != Controller.Output_AGENT_ID() { // 중복시 추가 안함
			tmp_ = append(tmp_, value)
		} else {
			remove_check = true
		}
	}

	as.Agents = tmp_

	return remove_check
}

func (as *Sharing) Output_Agent_Controller_with_ID(Agent_ID string) *agent_manager.Agent_Controller {

	as.agents_mutex.Lock()
	defer as.agents_mutex.Unlock()

	for _, value := range as.Agents {
		if Agent_ID == value.Output_AGENT_ID() { // 중복시 추가 안함
			return value
		}
	}

	return nil

}

// 연결된 에이전트 ID 반환
func (as *Sharing) Output_Agent_Controller() map[string]interface{} {

	as.agents_mutex.Lock()
	defer as.agents_mutex.Unlock()

	agents := map[string]interface{}{}
	agents["agents"] = []map[string]interface{}{}

	for _, value := range as.Agents {

		// 상태 추가
		agents["agents"] = append(
			agents["agents"].([]map[string]interface{}),
			value.Output_AGENT_INFO(), // 에이전트 정보 반환
		)
	}

	/*
		{
			"agents": [
				{
					"agent_id": "에이전트 ID",
					"is_connected": true or false
				}
			]
		}
	*/

	return agents

}
