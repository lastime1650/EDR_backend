from mitmproxy import http, ctx

import threading
import time
import os
import signal

# 수리카타
from NDR.suricata.suricata import SuricataManager

# --- mitmproxy 애드온 로직 ---
class NDR:
    def __init__(self):
        self.SuricataManager = SuricataManager(
            interface_ip="192.168.0.11", # test
        )
        pass

    def load(self, loader):
        """mitmproxy 애드온이 로드될 때 호출됨 (최초 1회)"""
        print("MitmProxy 로드됨.")
        
        print("수리카타 백그라운드 실행")
        self.SuricataManager.Start_Monitoring()
        
        # signal 등록
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        
        
    def done(self):
        """mitmproxy가 종료될 때 호출됨 (정리 작업)"""
        print("done")
        import subprocess
        
        # 수리카타 종료
        self.SuricataManager.Shutdown()
        
        # iptables 초기화
        from NDR.suricata.iptables import clean_iptables
        clean_iptables()
        
    # SIGTERM 처리
    def signal_handler(self, signal, frame):
        print("SIGNAL TERMINATED")
        self.done()

    # --- 표준 mitmproxy 이벤트 핸들러들 ---
    def request(self, flow: http.HTTPFlow) -> None:
        # mitmproxy를 통과하는 HTTP/S 요청 처리
        client_ip = flow.client_conn.address[0]
        # ctx.log.info(f"[MITMPROXY HANDLER] Request from {client_ip} to {flow.request.pretty_url}")
        # Scapy 스레드와 정보를 공유하려면 Queue나 다른 IPC 메커니즘 사용 고려
        print(f"[MITMPROXY HANDLER] Request from {client_ip} to {flow.request.pretty_url}")


    def response(self, flow: http.HTTPFlow) -> None:
        # mitmproxy를 통과하는 HTTP/S 응답 처리
        # ctx.log.info(f"[MITMPROXY HANDLER] Response for {flow.request.pretty_url}")
        print(f"[MITMPROXY HANDLER] Response for {flow.request.pretty_url}")

# mitmproxy가 로드할 애드온 인스턴스
addons = [
    NDR()
]