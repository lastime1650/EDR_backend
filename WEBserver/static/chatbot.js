
function getCookie(cookieName) {
    cookieName = cookieName + '=';
    let cookieData = document.cookie;
    let start = cookieData.indexOf(cookieName);
    let cookieValue = '';
    if (start != -1) {
        start += cookieName.length;
        let end = cookieData.indexOf(';', start);
        if (end == -1) end = cookieData.length;
        cookieValue = cookieData.substring(start, end);
    }

    return decodeURIComponent(cookieValue);
}



// LLM 서버에 있는 웹 소켓간 연결 수행
//const cookieValue = "{{ cookie }}"; // 쿠키 설정
//const cookieValue = getCookie("EDR_COOKIE_KEY");



// server정보
//const ws_serverip = "ws://192.168.0.1:9008/ws";
const ws_serverip = window.websocket_connection_url; // 진자로 받음


// WebSocket 연결 생성
const websocket = new WebSocket(ws_serverip); // 연결 시도


// 연결이 열렸을 때 실행되는 이벤트 핸들러
websocket.onopen = function(event) {

    websocket.send(getCookie("EDR_COOKIE_KEY"));

};

// 챗봇 폼에 메시지 추가 함수
function addMessage(sender, message, isUser = false) {
    message = message.replace(/\n/g, '<br>');

    const chatBody = document.getElementById('chatBody');
    const messageDiv = document.createElement('div');

    messageDiv.classList.add('chat-message')
    ;
    if (isUser) {
        messageDiv.classList.add('user');
    }
        messageDiv.innerHTML = `<span class="sender">${sender}:</span> <span class="message">${message}</span>`;
        chatBody.appendChild(messageDiv);
        chatBody.scrollTop = chatBody.scrollHeight; // 스크롤을 맨 아래로
    }

    // 메시지를 받았을 때 실행되는 이벤트 핸들러 (이 부분 수정)
    websocket.onmessage = function(event) {
        //alert(event.data);
        //console.log("Received message from server:", event.data);
        // 서버로부터 받은 데이터가 JSON 형식인지 TEXT인지 검증
        try {

          received_data = JSON.parse(event.data);

          if (received_data.cmd == "WEB_create_html_for_a_user") {
            // 생성된 HTML 코드를 추가
            const encodedHtmlCode = encodeURIComponent(received_data.data);
            window.location.href = `/llm_create_page?HTML_CODE=${encodedHtmlCode}`;

          }
          else if (received_data.cmd == "WEB_redirect_the_page") {
            // 페이지 리다이렉션
            //alert("리다이렉트 요청 받음");
            window.location.href = received_data.data;
          }
          else if (received_data.cmd == "init"){
            // 초기 통신
            if (received_data.data.length > 0){
              // 길이가 1 이상인 경우에 추가
              for (let i = 0; i < received_data.data.length; i++) {
                addMessage("You", received_data.data[i].user,true);
                addMessage("Bot", received_data.data[i].ai);
              }
            }else{
                //alert("이전 대화 이력이 없습니다.");
            }

          }else{
            addMessage("Bot", event.data);
          }

        } catch (e) {
          // JSON실패인 경우
          //alert("JSON 파싱 실패! 원본 메시지: " + event.data);
          // 또는 이는 LLM의 일반 메시지일 수 있다.
          addMessage("Bot", event.data);
        }
        return;
    };

// 에러가 발생했을 때 실행되는 이벤트 핸들러
websocket.onerror = function(event) {
    console.error("WebSocket error:", event);
    addMessage("Bot", "챗봇 서버와 연결이 끊겼습니다.");
};

// 연결이 닫혔을 때 실행되는 이벤트 핸들러
websocket.onclose = function(event) {
    console.log("WebSocket connection closed:", event);
    addMessage("Bot", "챗봇 서버와 연결이 끊겼습니다.");
};

// 챗봇 토글 및 메시지 전송 로직
const chatToggle = document.getElementById('chatToggle');
const chatForm = document.getElementById('chatForm');

chatToggle.addEventListener('click', () => {
    chatForm.classList.toggle('open');
});

const chatInput = document.getElementById('chatInput');
chatInput.addEventListener('keypress', (event) => {
	if (event.key === 'Enter') {
	  const message = chatInput.value.trim();
	  if (message !== '') {
		addMessage('You', message, true);
		chatInput.value = '';

		// 현재 자기가 접속한 페이지 경로
		const url = new URL(window.location.href);
		const decodedPathAndParams = decodeURIComponent(url.pathname + url.search);
		const current_page = decodedPathAndParams;

		const message_data = {
		  user: message, // 사용자가 보낼 메시지
		  current_page: current_page, // 현재 자신이 접속하고 있는 페이지
		  cookie: getCookie("EDR_COOKIE_KEY") // 쿠키 값
		}
		const jsonString = JSON.stringify(message_data);

		websocket.send(jsonString); // WebSocket을 통해 JSON 메시지 전송
	  }
	}
});