import json, requests
from typing import Optional, Any, List, Dict


def Add_Default_Script_2_Analysis_Server(input_script_api_dict:Dict):
    headers = {'Content-Type': 'application/json'}
    r = requests.post('http://127.0.0.1:5070/API/Script_Register', headers=headers, data=json.dumps(input_script_api_dict)).text
    print(r)
    return


def Init_Input_Script():
    # 파일 타입 생성
    file_type_script_code_Path = r"C:\Users\Administrator\Desktop\My_Python_Prj\NewGen_EDR\pythonProject\_Analysis_Server_\default_script_setting\Default_File_Type\sample_file_type_script.py"
    file_type_script_code = ""
    with open(file_type_script_code_Path, "r", encoding='utf-8') as f:
        file_type_script_code = str( f.read() )

    req = {
        "SCRIPT_NAME": "default1",
        "SCRIPT_TYPE": "file",
        "SCRIPT_PYTHON_CODE": file_type_script_code
    }
    Add_Default_Script_2_Analysis_Server(req)


    # 네트워크 타입 생성
    network_type_script_code_Path = r"C:\Users\Administrator\Desktop\My_Python_Prj\NewGen_EDR\pythonProject\_Analysis_Server_\default_script_setting\Default_Network_Type\sample_network_type_script.py"
    network_type_script_code = ""
    with open(network_type_script_code_Path, "r", encoding='utf-8') as f:
        network_type_script_code = str( f.read() )

    req = {
        "SCRIPT_NAME": "default2",
        "SCRIPT_TYPE": "network",
        "SCRIPT_PYTHON_CODE": network_type_script_code
    }
    Add_Default_Script_2_Analysis_Server(req)