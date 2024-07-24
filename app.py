from flask import Flask, request, render_template
from docker import from_env
from threading import Timer
from datetime import datetime, timedelta

app = Flask(__name__)

# Docker 클라이언트 초기화
docker_client = from_env()

session_dict = {} # 세션 : port 
container_dict = {} # 세션 : 컨테이너
timer_dict = {} # 세션 : 타이머
last_restart_time = {}  # 세션 : 마지막 재생성 시간

# 포트 범위
PORT_RANGE_START = 21000
PORT_RANGE_END = 21200

# 컨테이너 지속 시간 (초단위)
REMAINING_TIME = 1800
# 재시작 가능 시간 (초단위)
RESTART_TIME = 30

# 연결할 포트
CONNECT_PORT = 8000

# 도커 이미지
DOCKER_IMAGE = "kmc0487/svgphoto"

def remove_container(container_id, session_id):
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        print(f"Container {container_id} stopped and removed")
        
        # 세션 정보 삭제
        if session_id in session_dict:
            del session_dict[session_id]
        if session_id in container_dict:
            del container_dict[session_id]
            
        return None
    
    except:
        return "Error removing Conatiner! Admin에게 연락주세요"
        
def start_new_container(session_id):
    # 사용 가능한 포트 찾기
    isFull = True
    for p in range(PORT_RANGE_START, PORT_RANGE_END+1):
        if p not in session_dict.values():
            port = p
            isFull = False
            break

    if isFull:
        return "실행 가능한 port가 없습니다. Admin에게 연락주세요", None

    # Docker 컨테이너 생성 및 실행
    try:
        container = docker_client.containers.run(
            DOCKER_IMAGE, 
            detach=True,
            ports={f'{CONNECT_PORT}/tcp': port}
        )
    except:
        return "Error start Container! Admin에게 연락해주세요", None

    # 세션 및 포트 정보 저장
    session_dict[session_id] = port
    container_dict[session_id] = container.id

    # 30분 후 컨테이너 삭제
    timer = Timer(REMAINING_TIME, remove_container, [container.id, session_id])
    timer.start()
    timer_dict[session_id] = timer

    return None, port

def can_restart(session_id):
    now = datetime.now()
    if session_id not in last_restart_time:
        return True
    last_time = last_restart_time[session_id]
    if now - last_time > timedelta(seconds=RESTART_TIME):
        return True
    return False

@app.route('/', methods=['GET', 'POST'])
def index():
    session_id = request.cookies.get('session')
    
    if(request.method=='GET'):
        if not session_id:
            return "워게임 사이트 로그인을 해주세요"
    
        if session_id in session_dict.keys():
            port = session_dict[session_id]
            return render_template('instance.html', port=port, notice = None)
        else:
            return render_template('index.html')
    elif(request.method =='POST'):
        if session_id in session_dict.keys():
            port = session_dict[session_id]
            return render_template('instance.html', port=port, notice = None)
        last_restart_time[session_id] = datetime.now()
        error, port = start_new_container(session_id)
        if error:
            return error

        return render_template('instance.html', port=port)
    
@app.route("/restart", methods=['POST'])
def restart():
    session_id = request.cookies.get('session')
    
    if not session_id or session_id not in session_dict:
        return "세션이 유효하지 않습니다. 로그인을 확인해주세요"
    
    if not can_restart(session_id):
        return "<script>alert('30초가 지나야 재생성할 수 있습니다. 잠시 후 다시 시도해주세요.'); location.href='/';</script>"
    
    last_restart_time[session_id] = datetime.now()
    containerID = container_dict[session_id]
    
    if containerID:
        error = remove_container(containerID, session_id)
        if error:
            return error
    
    if session_id in timer_dict:
        timer_dict[session_id].cancel()
        del timer_dict[session_id]
        
    error, new_port = start_new_container(session_id)
    if error:
        return error
    
    return render_template('instance.html', port=new_port, notice = "컨테이너 재생성이 완료됐습니다!")
    
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=9000)
