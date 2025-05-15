package processmanagement

import (
	"CoreServer/util"
	"fmt"
)

// 주 목적: 프로세스 라이프 사이클 ID 추적용

type Process_Manager struct {
	processes  []*Process_struct
	seedobject *util.Seed
}

func New_Process_Manager(seedobj *util.Seed) *Process_Manager {
	return &Process_Manager{
		processes:  []*Process_struct{},
		seedobject: seedobj,
	}
}

// 프로세스 라이프 사이클 ID 자동 할당 또는 기존 가져오기

type Basic_cycle_info struct {
	Process_life_cycle_id             string // PID 대용
	My_parent_Process_life_cycle_id   string // 자신의 직계 부모
	Root_parent_Process_life_cycle_id string // 최초의 부모 사이클ID (최상위)
	//
	Root_is_running_by_user bool // 유저가 실행한 프로세스인가? (최초시점에서만 유효)
	//
	Is_child bool // 자식인가? ->(최상위 ROOT가 아닌 경우는 다 '자식'취급)
}

type Cycle_Info struct {
	My_Parent_cycle_info *Basic_cycle_info // 자신의 부모가 가지고 있는 사이클 정보
	My_cycle_info        *Basic_cycle_info // 내가 가지고 있는 사이클 정보
}

type Process_struct struct {
	PID            uint64
	Is_alive       bool
	process_struct []*Process_struct
	cycle_info     *Cycle_Info
}

// 그냥 자신의 PID만 가지고 있을 때,
func (as *Process_Manager) Get_process_life_cycle_ID(PID uint64) (*Cycle_Info, error) {
	cycle := as.Find_My_Process(PID, 0, &as.processes) // 자신의 객체를 반환 ( 없으면 생성, 부모를 찾으면서,, )
	if cycle != nil {
		return cycle, nil
	}

	// object를 못찾은 경우,,,,,,,
	return nil, fmt.Errorf("없음")
}

// 부모가 명시되어 있을때
func (as *Process_Manager) Get_process_life_cycle_ID_with_PPID(PID uint64, PPID uint64, is_running_by_user bool, is_process_creation bool) (*Cycle_Info, error) {
	//for _, object := range as.processes {
	//	if object.PID == PID && object.Is_alive {
	//		return object.Process_life_cycle_id
	//	}
	//}
	cycle := as.Find_My_Process(PID, PPID, &as.processes) // 자신의 객체를 반환 ( 없으면 생성, 부모를 찾으면서,, )
	if cycle != nil {
		return cycle, nil
	}

	if !is_process_creation {
		// 프로세스 제거인 경우도, 제거되기전의 프로세스 정보가 없으므로 생성의 의미가 없음
		return nil, fmt.Errorf("프로세스 제거이벤트지만 이전의 생성 정보가 없어서 모니터링 안함")
	}

	// 아직 'Process_life_cycle_id' 값이 없는 경우임
	new_process_life_cycle_id := util.Hash_to_String(util.Get_SHA512(as.seedobject.Get_Random_Byte(12412)))

	// 사이클 정보 생성
	my_cycle := &Cycle_Info{
		My_Parent_cycle_info: nil, // 자신이 root 프로세스이므로 nil (최초 조상)
		My_cycle_info: &Basic_cycle_info{
			Process_life_cycle_id:             new_process_life_cycle_id,
			My_parent_Process_life_cycle_id:   new_process_life_cycle_id,
			Root_parent_Process_life_cycle_id: new_process_life_cycle_id,
			Root_is_running_by_user:           is_running_by_user,
			Is_child:                          false,
		}, // 자신의 정보
	}

	created_new_ := Process_struct{
		PID:      PID,
		Is_alive: true,
		//Process_life_cycle_id: new_process_life_cycle_id, // 자기자신 사이클 ID
		process_struct: []*Process_struct{},

		//my_parent_Process_life_cycle_id:   new_process_life_cycle_id, // 부모가 자기자신임 (취급)
		//root_parent_Process_life_cycle_id: new_process_life_cycle_id, // 최초 부모가 자기자신임
		//root_is_running_by_user:           is_running_by_user,

		//is_child: false,

		cycle_info: my_cycle,
	}
	as.processes = append(as.processes, &created_new_)

	return created_new_.cycle_info, nil
}

func (as *Process_Manager) Find_My_Process(PID uint64, PPID uint64, process_struct_ *[]*Process_struct) *Cycle_Info {

	for _, Parent := range *process_struct_ {
		if Parent.PID == PID && Parent.Is_alive {
			return Parent.cycle_info
		} else if Parent.PID == PPID && Parent.Is_alive {
			// 자신의 부모에 대한 객체가 이미 있는 경우, 자신의 객체(자식)를 생성하고 부모에 속하도록 한다.

			/*
				new_child_object := &Process_struct{
					PID:                               PID,
					Is_alive:                          true,
					Process_life_cycle_id:             util.Hash_to_String(util.Get_SHA512(as.seedobject.Get_Random_Byte(12412))),
					my_parent_Process_life_cycle_id:   object.Process_life_cycle_id,             // 자신의 직계부모 사이클ID를 가지고 다닌다.
					root_parent_Process_life_cycle_id: object.root_parent_Process_life_cycle_id, // 최초 조상 사이클ID를 가지고 다닌다.
					root_is_running_by_user:           object.root_is_running_by_user,           // 최초 조상 프로세스에서 보았을 때, 유저가 최초 실행했는가?
					process_struct:                    make([]*Process_struct, 0),
					is_child:                          true,
				}
				Parent.process_struct = append(Parent.process_struct, new_child_object)*/

			// 아직 'Process_life_cycle_id' 값이 없는 경우임
			new_process_life_cycle_id := util.Hash_to_String(util.Get_SHA512(as.seedobject.Get_Random_Byte(12412)))

			// 사이클 정보 생성
			my_cycle := &Cycle_Info{
				My_Parent_cycle_info: Parent.cycle_info.My_cycle_info,
				My_cycle_info: &Basic_cycle_info{
					Process_life_cycle_id:             new_process_life_cycle_id,
					My_parent_Process_life_cycle_id:   Parent.cycle_info.My_cycle_info.Process_life_cycle_id,             // 직계 부모의  'Process_life_cycle_id' 것을 물려받는다.
					Root_parent_Process_life_cycle_id: Parent.cycle_info.My_cycle_info.Root_parent_Process_life_cycle_id, // 조상의 것을 물려받는다
					Root_is_running_by_user:           Parent.cycle_info.My_cycle_info.Root_is_running_by_user,           // 조상의 것을 물려받는다.
					Is_child:                          true,                                                              // 자신의 상태 ( 또는 부모 )
				},
			}

			new_child_object := Process_struct{
				PID:      PID,
				Is_alive: true,

				process_struct: []*Process_struct{},

				cycle_info: my_cycle,
			}
			Parent.process_struct = append(Parent.process_struct, &new_child_object)
			//as.processes = append(as.processes, &new_child_object)

			return new_child_object.cycle_info //
		}

		cycle_ := as.Find_My_Process(PID, PPID, &Parent.process_struct)
		if cycle_ != nil {
			return cycle_
		}
	}
	return nil
}

func (as *Process_Manager) Set_process_terminate(PID uint64) (bool, string, string, string) {
	return as.Terminate_process(PID, &as.processes)
}
func (as *Process_Manager) Terminate_process(PID uint64, process_struct_ *[]*Process_struct) (bool, string, string, string) {

	for _, mine := range *process_struct_ {
		if mine.PID == PID && mine.Is_alive {
			mine.Is_alive = false

			my_cycle_id := mine.cycle_info.My_cycle_info.Process_life_cycle_id
			parent_cycle_id := mine.cycle_info.My_cycle_info.My_parent_Process_life_cycle_id
			root_parent_Process_life_cycle_id := mine.cycle_info.My_cycle_info.Root_parent_Process_life_cycle_id

			//*process_struct_ = append((*process_struct_)[:i], (*process_struct_)[i+1:]...)
			return true, my_cycle_id, parent_cycle_id, root_parent_Process_life_cycle_id
		}

		if res, my_cycle_id, parent_cycle_id, root_parent_Process_life_cycle_id := as.Terminate_process(PID, &mine.process_struct); res {
			return true, my_cycle_id, parent_cycle_id, root_parent_Process_life_cycle_id
		}
	}

	return false, "?", "?", "?"
}

//
