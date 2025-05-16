package sql

import (
	"database/sql"
	"fmt"
	"log"

	_ "github.com/go-sql-driver/mysql"
)

type Mysql struct {
	mysql *sql.DB
}

func New_Mysql(serverIP string, port int, dbUser string, dbPassword string, dbname string) *Mysql {
	// Step 1: dbname 없이 먼저 연결
	connect_info := fmt.Sprintf("%s:%s@tcp(%s:%d)/", dbUser, dbPassword, serverIP, port)
	db, err := sql.Open("mysql", connect_info)
	if err != nil {
		log.Fatalf("초기 DB 연결 실패: %v", err)
		return nil
	}

	// Step 2: DB 생성
	_, err = db.Exec(fmt.Sprintf("CREATE DATABASE IF NOT EXISTS %s", dbname))
	if err != nil {
		log.Fatalf("데이터베이스 생성 실패 또는 이미 존재함!: %v", err)
		return nil
	}

	// Step 3: 생성된 DB로 다시 연결
	connect_info_with_db := fmt.Sprintf("%s:%s@tcp(%s:%d)/%s", dbUser, dbPassword, serverIP, port, dbname)
	db_with_db, err := sql.Open("mysql", connect_info_with_db)
	if err != nil {
		log.Fatalf("DB 연결 실패 (dbname 포함): %v", err)
		return nil
	}

	fmt.Println("DB 연결 성공")
	return &Mysql{
		mysql: db_with_db,
	}
}

// Query 쿼리 -> 결과값 반환
func (as *Mysql) Query(query string) ([]map[string]interface{}, error) {

	queried_data, err := as.mysql.Query(query)
	if err != nil {
		return nil, err
	}

	defer queried_data.Close()

	cols, _ := queried_data.Columns()
	cols_len := len(cols)

	output := []map[string]interface{}{}

	for queried_data.Next() {

		rowMap := make(map[string]interface{})
		scanArgs := make([]interface{}, cols_len)
		values := make([]interface{}, cols_len)

		for i := range cols {
			scanArgs[i] = &values[i] // 다음 Scan()를 통해 얻어오는 "주소"를 scanArgs에 넣음
		}
		// scanArgs에 미리 준비된 요소 크기를 인수로 넣어서 값을 받아온다.
		if err := queried_data.Scan(scanArgs...); err != nil {
			return nil, err
		}

		// values에 정리
		for i, colName := range cols {
			val := values[i] // Scan으로부터 얻은 주소로부터 실제 값을 가져옴
			if b, ok := val.([]byte); ok {
				rowMap[colName] = string(b)
			} else {
				rowMap[colName] = val
			}
		}

		// 축적
		output = append(output, rowMap)

	}

	if len(output) == 0 {
		return nil, nil
	}

	return output, nil
}

// Exec 실행 -> 확인여부(error) 반환
func (as *Mysql) Exec(query string) error {

	if _, err := as.mysql.Exec(query); err != nil {
		return err
	}

	return nil
}
