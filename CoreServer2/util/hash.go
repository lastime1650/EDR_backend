package util

import (
	"crypto/sha256"
	"crypto/sha512"
	"encoding/hex"
	"time"
)

func get_current_timestamp_for_hash_seed() int64 {

	_, RegionTimestamp_int64 := GetCurrentRegionTime("Asia/Seoul")

	return getCurrentTimestamp() + RegionTimestamp_int64
}

func getCurrentTimestamp() int64 {
	return time.Now().Unix()
}

func Get_SHA256(data any) []byte {

	retn_hash := [32]byte{}

	switch t := data.(type) {
	case []byte:
		retn_hash = sha256.Sum256([]byte(t))
	case string:
		retn_hash = sha256.Sum256([]byte(string(t)))
	default:
		return nil
	}

	return retn_hash[:]
}

func Get_SHA512(data any) []byte {

	retn_hash := [64]byte{}

	switch t := data.(type) {
	case []byte:
		retn_hash = sha512.Sum512([]byte(t))
	case string:
		retn_hash = sha512.Sum512([]byte(string(t)))
	default:
		return nil
	}

	return retn_hash[:]
}

func Hash_to_String(data []byte) string {
	return hex.EncodeToString(data)
}

func GetCurrentRegionTime(region string) (string, int64) {
	// "Asia/Seoul" 타임존 로드
	loc, err := time.LoadLocation("Asia/Seoul")
	if err != nil {
		// 에러 처리 (예: 타임존 로드 실패 시 패닉)
		panic(err)
	}

	// 현재 시간을 "Asia/Seoul" 타임존으로 변환
	seoulTime := time.Now().In(loc)

	// 원하는 형식으로 포맷팅
	return seoulTime.Format("2006-01-02 15:04:05"), seoulTime.Unix()
}
