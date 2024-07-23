from flask import Flask, request
from docker import from_env
from threading import Timer
import os

app = Flask(__name__)

# Docker 클라이언트 초기화
docker_client = from_env()

# 세션 관리용 사전
session_dict = {}
# 세션 : 포트

# 포트 범위
PORT_RANGE_START = 21000
PORT_RANGE_END = 21200

def remove_container(container_id, session_id):
    """지정된 컨테이너를 중지 및 삭제하는 함수"""
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        print(f"Container {container_id} stopped and removed")
        
        # 세션 정보 삭제
        if session_id in session_dict:
            del session_dict[session_id]
            print(f"Session {session_id} removed from session_dict")
    except Exception as e:
        print(f"Error removing container {container_id}: {e}")

@app.route('/')
def index():
    session_id = request.cookies.get('session')
    if not session_id:
        return "워게임 사이트 로그인을 해주세요"
    
    if session_id in session_dict.keys():
        port = session_dict[session_id]
        return f"http://haf.world:{port}로 접속해주세요"
    else:
        # 20000-20500 범위에서 랜덤 포트 선택
        isFull = True
        for p in range(PORT_RANGE_START, PORT_RANGE_END+1):
            if p not in session_dict.values():
                port = p
                isFull = False
                break
            
        if isFull==True:
            return "실행 가능한 port가 없습니다. 관리자에게 문의해주세요"
        
        # Docker 컨테이너 생성 및 실행
        container = docker_client.containers.run(
            "kmc0487/svgphoto", 
            detach=True,
            ports={'8000/tcp': port}
        )
        
        # 세션 및 포트 정보 저장
        session_dict[session_id] = port

        # 30분 후 컨테이너 삭제
        Timer(30, remove_container, [container.id, session_id]).start()

        # 세션 쿠키 설정
        return f"http://haf.world:{port}로 접속해주세요"

app.run(host="0.0.0.0", port=20018)