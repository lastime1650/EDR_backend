package util

import (
	"fmt"
	"math/rand/v2"
	"sync"
	"time"
)

// rand.NewChaCha8을 사용하며, Seed는 util.hash의 unix 타임을 통해서 구현한다.
type Seed struct {
	Reserved int64
	mutex    *sync.Mutex
}

func New_Seed() *Seed { // [Update] - 너무 스레드가 빨라서 'Instance_ID'가 중복되는 현상이 발생하는 것을 방지하기 위해; 1씩 증가하는 값 추가.
	return &Seed{
		Reserved: 0,
		mutex:    &sync.Mutex{},
	}
}

func (as *Seed) Get_Random_Byte(n int) []byte {

	as.mutex.Lock()
	defer as.mutex.Unlock()

	if as.Reserved > 9223372036854775800 {
		as.Reserved = 0
	}

	if bytedata, err := Int64_to_Bytes(get_current_timestamp_for_hash_seed() + as.Reserved); err == nil {
		seed := [32]byte{0}
		copy(seed[:], bytedata)

		if random_instance := rand.NewChaCha8(seed); random_instance != nil { // 문제 1
			random_byte := make([]byte, n)
			if input_read, err := random_instance.Read(random_byte); err == nil {
				if input_read == n {
					as.Reserved++
					return random_byte
				} else {
					as.Reserved++
					return nil
				}
			}
		}
	}

	return nil
}

// 현재 global 시간
func Getglobaltime() (string, error) {
	// 서울의 타임존 가져오기
	location, err := time.LoadLocation("Asia/Seoul")
	if err != nil {
		return "", fmt.Errorf("Error:", err)
	}

	// 현재 시간 가져오기
	seoulTime := time.Now().In(location)

	// 시간 반환
	return seoulTime.Format("2006-01-02 15:04:05"), nil
}

func GetTimestamp_iso8601() (string, error) {
	// 서울의 타임존 가져오기
	location, err := time.LoadLocation("Asia/Seoul")
	if err != nil {
		return "", fmt.Errorf("Error:", err)
	}

	// 현재 시간 가져오기
	seoulTime := time.Now().In(location)

	// 시간 반환
	return seoulTime.Format("2006-01-02T15:04:05.000Z"), nil
}
