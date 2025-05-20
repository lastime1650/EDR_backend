import hashlib
import queue
from typing import Optional
import base64


from Tool_Management.Tools.Tool_Yara.Yara import Yara_Analyzer
from Tool_Management.Tools.Tool_Sigcheck.Sigcheck import Check_sign_exe
from Tool_Management.Tools.Tool_Malwarebazaar.MalwareBazaar import MalwareBazaar
from Tool_Management.Tools.Tool_Virustotal.Virustotal import VirusTotal_analysis

from Tool_Management.Tools.Tool_URLhaus.URLhaus import URLhaus_for_provider

class ToolManager:
    def __init__(self):
        
        self.Yara = Yara_Analyzer() # 야라 도구
        # sigcheck는 함수
        self.MalwareBazaar = MalwareBazaar() # 매니저 도구
        self.VirusTotal = VirusTotal_analysis() # 비동기 분석 도구
        self.URLhaus = URLhaus_for_provider() # 비동기 분석 도구
    
    # Yara
    def Yara_Analysis(self, analysis_target_bin: bytes)->queue.Queue:
        return self.Yara.Start_Analysis(binary=analysis_target_bin) # 야라 비동기 요청
    
    # Sigcheck
    def Sigcheck_Analysis(self, analysis_target_bin: bytes)->bool:
        return Check_sign_exe(file=analysis_target_bin )
    
    # VirusTotal
    def VirusTotal_Analysis(self, VirusTotal_API_KEY:str, File_Binary:bytes, option_SHA256:str=None)->queue.Queue:
        return self.VirusTotal.Start_Analysis(VirusTotal_API_KEY,File_Binary,option_SHA256)
    
    # MalwareBazaar
    def MalwareBazaar_Analysis(self, File_HASH256:str)->queue.Queue:
        return self.MalwareBazaar.SHA256_query_get_info(File_HASH256)
    
    # URLhaus
    def URLhaus_Analysis(self, analysis_target_IP:str)->queue.Queue:
        return self.URLhaus.Start_Analysis(analysis_target_IP)
    
    # # # # # # [Utility] # # # # # #
    # 1. BASE64 -> Binary
    def BASE64_to_Binary(self, BASE64_data:str)->Optional[bytes]:
        try:
            return base64.b64decode(BASE64_data)
        except:
            return None
    # 2. Binary -> SHA256
    def Binary_to_SHA256(self, Binary_data:bytes)->Optional[str]:
        try:
            return hashlib.sha256(Binary_data).hexdigest()
        except:
            return None

    # 3. Binary -> Size
    def Binary_to_Size(self, Binary_data:bytes)->Optional[int]:
        try:
            return len(Binary_data)
        except:
            return None