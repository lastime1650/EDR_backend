package util

import (
	"fmt"
	"os"
	"path/filepath"
	"sync"
)

/*파일 입출력을 관리함.*/
/*
	조심해야하는건 비동기화 적으로 호출하므로,
	queue기반으로 충돌을 방지하도록 해야한다.
*/
type File_io struct {
	mutex    sync.Mutex // 파일 쓰기 및 읽기에 관한 동기화 과정
	Root_Dir string     // 파일 저장을 위한 루트 디렉토리
}

func New_File_io(Root_Dir string) *File_io {

	// 디렉터리 확인 여부후 생성
	if _, err := os.Stat(Root_Dir); os.IsNotExist(err) {
		os.MkdirAll(Root_Dir, 0777)
	}

	return &File_io{
		mutex:    sync.Mutex{},
		Root_Dir: Root_Dir,
	}
}

// 파일 읽기
func (as *File_io) Read_File(filename string) ([]byte, error) {

	is_exist := false

	as.mutex.Lock()
	defer as.mutex.Unlock()

	filename = filepath.Join(as.Root_Dir, "/", filename)

	is_exist = as.Check_File_Exist(filename)

	//filename = as.Root_Dir + filename

	if is_exist {
		return os.ReadFile(filename)
	} else {
		return nil, fmt.Errorf("읽을 파일이 없습니다")
	}
}

// 파일 쓰기
func (as *File_io) Write_File(filename string, data []byte, is_overwrite bool) (bool, error) {

	// 이미지 파일이 존재한 경우 쓰지 않도록 조치한다.
	is_exist := false

	as.mutex.Lock()
	defer as.mutex.Unlock()

	filename = filepath.Join(as.Root_Dir, "/", filename)

	is_exist = as.Check_File_Exist(filename)

	//filename = as.Root_Dir + filename

	if is_exist {
		if is_overwrite {
			perm := os.FileMode(os.O_CREATE | os.O_EXCL | 0777)
			return true, os.WriteFile(filename, data, perm)
		} else {
			return false, fmt.Errorf("이미 존재하는 파일이 있으므로 덮어쓰지 않겠습니다.")
		}

	} else {
		perm := os.FileMode(os.O_CREATE | os.O_EXCL | 0777)
		return true, os.WriteFile(filename, data, perm)
	}
}

// 파일 체크
func (as *File_io) Check_File_Exist(fullpath string) bool {
	//fmt.Printf("파일찾기 -> %s \n", fullpath)
	if _, err := os.ReadFile(fullpath); err != nil {
		return false
	}
	return true
}
