# 현 디렉터리에 대한 작업을 함
# 현 디렉터리에 대한 정보를 얻어오거나, 파일을 생성하거나 삭제하는 작업을 함
import os
import threading
import time
from typing import Optional


def loop_scan_file_from_dir_with_extension(dir_path, extension):

    result = []

    for root, dirs, files in os.walk(dir_path):
        for dir in dirs:
            #print(root+'\\'+dir)
            files += loop_scan_file_from_dir_with_extension(root+'\\'+dir, extension)

        #print([os.path.join(root, name) for name in files if name.endswith(extension)])
        tmp = [os.path.join(root, name) for name in files if str(name).endswith(extension)]
        print(len(tmp))
        if(len(tmp) > 0):
            result.append(tmp)
        '''
        for file in files:
            print(file)
            if file.endswith(extension):
                files.append(os.path.join(root, file))
        '''
        break

    return result


class File_Manager():
    def __init__(self, Current_Directory:str):
        self.Current_Directory = Current_Directory

        self.File_Mutex = threading.Lock()

    def Searching_Files(self, File_Extension_without_dot:str):

        searched_files = []

        '''
            현 디렉터리에서 특정 확장자를 가진 파일을 검색
        '''
        for root, dirs, files in os.walk(self.Current_Directory):
            #all_directories.append(root)
            #for dir_name in dirs:
            #    all_directories.append(os.path.join(root, dir_name))
            #for file_name in files:
            #    all_files.append(os.path.join(root, file_name))
            for name in files:
                if( name.endswith(File_Extension_without_dot) ): # 마지막 쪽 문자열 비교
                    searched_files.append(os.path.join(root,name))


        #print(searched_files)

        return searched_files

    def Searching_Directories(self ):

        searched_Directories = []

        '''
            현 디렉터리에서 하위 디렉터리 탐색
        '''
        for root, dirs, files in os.walk(self.Current_Directory):
            for dir_name in dirs:
                searched_Directories.append(os.path.join(root, dir_name))

        print(searched_Directories)

        return searched_Directories

    def Loop_Scan_File_From_Dir_With_Extension(self, Extension:str):

        return loop_scan_file_from_dir_with_extension(self.Current_Directory, Extension)

    def Change_Current_Directory(self, New_Directory:str):
        self.Current_Directory = New_Directory


    #파일이 존재하는 지 체크, 두번쨰 인자값이 True면 데이터로 추출할 수 있음
    def File_exist_check_or_get(self, File_Name:str, get_if_exist:bool)->(bool,bytes):

        with self.File_Mutex:
            for root, dirs, files in os.walk(self.Current_Directory):
                for file_name in files:
                    #print(os.path.join(root, file_name))
                    if(File_Name.lower() == file_name.lower()):
                        if(get_if_exist):
                            Output = b''

                            with open(str(os.path.join(root, file_name)), 'rb') as file:
                                Output = file.read()

                            return True, Output

                        else:
                            return True, b''

            return False, b''
    def File_Create_with_check(self, File_name:str, Input_File_bytes:bytes)->Optional[str]:

        with self.File_Mutex:
            if os.path.exists(self.Current_Directory+'\\'+File_name):
                #return None
                return self.Current_Directory+'\\'+File_name
            else:
                with open(self.Current_Directory+'\\'+File_name, 'wb') as file:
                    file.write(Input_File_bytes)
                time.sleep(0.1)
                if os.path.exists(self.Current_Directory + '\\' + File_name):
                    return f'{self.Current_Directory}\\{File_name}'
                else:
                    return None




#r = File_Manager(r"C:\Users\Administrator\Desktop\My_Python_Prj\NewGen_EDR\pythonProject\Analysis_System\Files").File_Create_with_check('test',b'1')
#print(r)