
#------- Yara ---------------------------------------------------------------------------------------------------------
import yara
from Tool_Management.Tools.FileManager import File_Manager # 파일 탐색기

#--
import threading, queue


# Yara Rule을 이용하여 파일을 분석한다.
class Yara_Analyzer:
    def __init__(self,Rules_folder_ROOT_path:str=r"/docker__AnalysisServer/Tool_Management/Tools/Tool_Yara/yara_rules"  ):

        self.yaraMutex = threading.Lock()


        self.Rules_folder_path = []
        
        self.Rules_folder_path = File_Manager(Rules_folder_ROOT_path).Searching_Files("yar")



    # 분석이 자동화로 시작할수 있는 기본 형식임 ( 이 메서드 이름과 인자는 절대 변경하면 안됨
    def Start_Analysis(self, binary:bytes=None, file_path:str=None):
        #print("yara")
        queue_inst = queue.Queue() # 이거 없어서 무조건 None
        thread = threading.Thread(target=self.Running, args=(queue_inst, binary, file_path))
        thread.start()
        return queue_inst


    def Running(self, queue_inst:queue.Queue, binary:bytes=None, file_path:str=None):

        result = {
            "yara_detected_by_rule": []
        }

        # 분석 대상 추출
        target_binary = b''
        if binary and isinstance(binary, bytes):
            target_binary = binary
        elif file_path and isinstance(file_path, str):
            target_binary = open(file_path, 'rb').read()
        else:
            queue_inst.put(None) # 결과 리턴
            return

        # rule 탐지 실시
        
        rule_detected_by_yara = []
        
        with self.yaraMutex:
            for yara_file in self.Rules_folder_path:

                # Yara 컴파일
                try:
                    yara_rule_instance = yara.compile(filepath=yara_file, externals={'max_strings_per_rule': 500})
                except:
                    continue
                
                # 매칭 실시
                matches = yara_rule_instance.match(data=target_binary)

                # 결과 추출
                if(len(matches)>0):
                    # rule 일치하였을 때
                    for matched_rule_name in matches:
                        rule_detected_by_yara.append({
                            "rule_name": str(matched_rule_name),
                            "description": matched_rule_name.meta["description"] if "description" in matched_rule_name.meta else "There is no description for this yara rule, but we can guess from the 'rule_name'",
                        })

        # 결과 정리
        if len(rule_detected_by_yara) > 0:
            result["yara_detected_by_rule"] = rule_detected_by_yara
        else:
            result = None
        queue_inst.put(result)

        return


'''# (1) 야라 분석 ROOT 폴더 지정
my_yara_inst = Yara_Analyzer()

# (2) 분석 대상 파일 지정 또는 바이너리 가능!
target: any = None
target = "C:\\Users\\Administrator\\Desktop\\KDU\\\kdu.exe"
target = open("C:\\Users\\Administrator\\Desktop\\KDU\kdu.exe", 'rb').read()

# (3) 비동기 분석 요청
queue_instance = my_yara_inst.Start_Analysis( binary=target)
print(f"요청 -> {len(target)}")
# (4) 분석 결과 얻어오기
yara_result = queue_instance.get() # 하나의 데이터만 기다리면 됩니다. !@
print(yara_result)'''


