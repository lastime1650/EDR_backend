import subprocess
import threading 
import json


from NDR.suricata.iptables import clean_iptables

class SuricataManager():
    def __init__(self, interface_ip:str):
        
        #1. NFQUEUE 설정
        
        # 1.1. iptables 초기화 
        #
        clean_iptables()
        
        # 1.2. iptables - FORWARD << NFQUEUE >> 설정
        subprocess.run(
            ["iptables", "-I", "FORWARD", "-j", "NFQUEUE", "--queue-num", "0"],
            check=False # 오류 발생해도 예외 발생 안 함
        )
        
        
        
        
    
    def Start_Monitoring(self  ):
        # suricata 실행
        
        
        # eve.json을 unix-stream으로 받아야한다.
        
        # 1. 먼저 리스닝 상태를 만들어야한다
        
        # 2. 수리카타를 실행해서 계속 실시간 json 이벤트를 받고 처리하면 된다. 
        
        
        # 1. eve 실시간 이벤트 리스닝 
        threading.Thread(
            target=self.Set_Receive_event,
            args=(
                "/var/run/suricata/eve.sock",
            ),
            daemon=True
        ).start()
        
        
        import time
        time.sleep(1)
        
        # suricata -c /etc/suricata/suricata.yaml -i {target_interface_name} -q 0 &
        subprocess.run(
            ["suricata", "-c", "/etc/suricata/suricata.yaml", "-q", "0", "&"],
            check=False
        )
        
        pass
    
    
    def Set_Receive_event(self, eve_sock_path:str):
        
        import os
        
        if os.path.exists(eve_sock_path):
            os.remove(eve_sock_path)
        
        import socket
            
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        print(f"Listening on socket {eve_sock_path}")
        s.bind(eve_sock_path)
        s.listen(1)

        conn, addr = s.accept()
        while True:
            data = conn.recv(4096).decode()
            if not data:
                break
            
            data_list:list[str] = data.split("\n")
            
            
            # 비동기 이벤트 처리
            threading.Thread(
                target=self.Processing_event,
                args=(
                    data_list,
                )
            ).start()
            
        
            
        print("수리카타 eve sock NONE받음")
        
        self.Shutdown()
        clean_iptables()
        quit()
    
    # suricata 이벤트 처리
    def Processing_event(self, data_list:list):
        
        # 빠르게 리턴해야함
        
        # 파싱
        
        # 1. 한 요소씩 가져와 JSON변환 후 Kafka 전달
        for data in data_list:
            
            if len(data) == 0:
                continue
            
            event_json = {}
            
            try:
                event_json = json.loads(data)
            except:
                continue
            
            print(event_json) # test 출력
            print("\n-----------\n")
            
    
    def Shutdown(self):
        
        # suricata 강제종료
        subprocess.run(
            ["pkill", "-f", "suricata"],
            check=False
        )
        