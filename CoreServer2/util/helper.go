package util

import (
	"log"
	"os"
)

// error 처리하는 함수
func ERROR_PROCESSING[T any](value T, err error) T {
	if err != nil {
		log.Fatal(err)
	}
	return value
}

// 환경변수 체크 후 없으면 디폴트 값 반환 함수
func Check_ENV(key string, default_value string) string {
	if value, exist := os.LookupEnv(key); exist {
		return value
	} else {
		return default_value
	}
}
