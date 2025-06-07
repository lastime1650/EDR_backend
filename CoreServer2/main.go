package main

import (
	"CoreServer/RestAPi"
	ShareObject "CoreServer/Share_Object"
	"CoreServer/agent"
	"CoreServer/util"
	"fmt"
	"log"
	"net"
	"os"
	"runtime"
	"strconv"
	"time"
)

func main() {

	// 시간대 체크
	loc, err := time.LoadLocation("Asia/Seoul")
	if err != nil {
		log.Fatalf("시간대 'Asia/Seoul'을 로드할 수 없습니다: %v", err)
	}
	nowInSeoul := time.Now().In(loc)
	fmt.Printf("현재 시간: %s\n", nowInSeoul.Format("2006-01-02T15:04:05.000"))

	// Docker 로부터 받을 환경변수

	// 데이터 베이스
	DB_HOST := os.Getenv("DB_HOST") // DB 서버 IP
	DB_PORT := os.Getenv("DB_PORT") // DB 서버 포트
	DB_USER := os.Getenv("DB_USER") // DB 서버 사용자 ( default -> root )
	DB_PASS := os.Getenv("DB_PASS") // DB 서버 사용자 비밀번호 ( defulat -> root , 1234 )

	if DB_HOST == "" {
		DB_HOST = "Database"
	}

	if DB_PORT == "" {
		DB_PORT = "3306"
	}
	if DB_USER == "" {
		DB_USER = "root"
	}
	if DB_PASS == "" {
		DB_PASS = "1234"
	}

	// 엘라스틱서치
	ELASTICSEARCH_HOST := util.Check_ENV("ELASTICSEARCH_HOST", "0.0.0.0") // 엘라스틱서치 서버 IP
	ELASTICSEARCH_PORT := util.Check_ENV("ELASTICSEARCH_PORT", "9200")    // 엘라스틱서치 서버 포트

	// 카프카
	KAFKA_HOST := util.Check_ENV("KAFKA_HOST", "0.0.0.0") // 카프카 서버 IP
	KAFKA_PORT := util.Check_ENV("KAFKA_PORT", "9092")    // 카프카 서버 포트

	// 분석 서버
	ANALYSIS_SERVER_HOST := util.Check_ENV("ANALYSIS_SERVER_HOST", "0.0.0.0") // 분석 서버 IP
	ANALYSIS_SERVER_PORT := util.Check_ENV("ANALYSIS_SERVER_PORT", "6060")    // 분석 서버 포트

	// 코어서버 RestAPI remote port
	RESTAPI_REMOTE_PORT := util.Check_ENV("RESTAPI_REMOTE_PORT", "10000") // 코어서버 RestAPI remote port

	// 에이전트 리시브 포트
	AGENT_RECEIVE_REMOTE_PORT := util.Check_ENV("AGENT_RECEIVE_REMOTE_PORT", "10299") // 에이전트 리시브 포트

	// local내 스토리지
	LOCAL_STORAGE_DIR := os.Getenv("LOCAL_STORAGE_DIR") // 에이전트로부터 파일 저장 하는 디렉토리
	if LOCAL_STORAGE_DIR == "" {
		LOCAL_STORAGE_DIR = "/CoreServer/save_file" // 기본값 ( '/CoreServer' 은 절대경로 )
	}

	fmt.Printf("받은 인자 값 출력 DB: %s:%s DB_USER: %s DB_PASS: %s ELASTICSEARCH_HOST: %s ELASTICSEARCH_PORT: %s KAFKA_HOST: %s KAFKA_PORT: %s ANALYSIS_SERVER_HOST: %s ANALYSIS_SERVER_PORT: %s LOCAL_STORAGE_DIR: %s \n",
		DB_HOST, DB_PORT, DB_USER, DB_PASS, ELASTICSEARCH_HOST, ELASTICSEARCH_PORT, KAFKA_HOST, KAFKA_PORT, ANALYSIS_SERVER_HOST, ANALYSIS_SERVER_PORT, LOCAL_STORAGE_DIR)

	runtime.GOMAXPROCS(runtime.NumCPU())

	share_object := ShareObject.New_Share_Object(
		DB_HOST,
		util.ERROR_PROCESSING(strconv.Atoi(DB_PORT)),
		DB_USER,
		DB_PASS,
		ELASTICSEARCH_HOST,
		util.ERROR_PROCESSING(strconv.Atoi(ELASTICSEARCH_PORT)),
		KAFKA_HOST,
		util.ERROR_PROCESSING(strconv.Atoi(KAFKA_PORT)),
		ANALYSIS_SERVER_HOST,
		uint32(util.ERROR_PROCESSING(strconv.Atoi(ANALYSIS_SERVER_PORT))),
		LOCAL_STORAGE_DIR,
	)
	fmt.Print("HELLO")
	/* [1/2] RestAPI 구동 시작 */
	RESTAPI_REMOTE_PORT_uint32 := uint32(util.ERROR_PROCESSING(strconv.Atoi(RESTAPI_REMOTE_PORT)))
	go RestAPi.Start_RestAPI_Server("0.0.0.0", RESTAPI_REMOTE_PORT_uint32, share_object) //

	/* [2/2] 에이전트 수신기 */

	// 1. TCP 소켓을 생성
	TCPaddr, err := net.ResolveTCPAddr("tcp", "0.0.0.0:"+AGENT_RECEIVE_REMOTE_PORT)
	if err != nil { // 예외 처리
		panic(err)
	}

	// 2. TCP 소켓을 연다.
	TCPconn, err := net.ListenTCP("tcp", TCPaddr)
	if err != nil { // 예외 처리
		panic(err)
	}

	// 3. TCP 소켓을 무한정 수신한다.
	for {
		fmt.Printf("에이전트 수신 대기 중..\n")
		TCPconn, err := TCPconn.AcceptTCP()
		if err != nil { // 예외 처리
			panic(err)
		}

		Agent_Manager := agent.New_Agent_Manager(TCPconn, share_object, util.New_Seed())

		// 공유변수에 {에이전트 컨트롤러}저장
		share_object.Append_Agent_Controller(
			Agent_Manager.Agent_Controller,
		)

		go Agent_Manager.Start_Agent_Communication()

		continue
	}

	/* 동작 중에 return 되어서는 안됨 */
}
