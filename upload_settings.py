"""USB 포트는 기본 자동 탐색. 보드 설정과 모터 극성은 실물에 맞추세요."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PORT = None  # Arduino/CH340 USB 포트 자동 탐색. 직접 지정하려면 "COM11".
# ATmega328P / Arduino UNO 호환 보드·부트로더 기준입니다.
# 실제 보드와 부트로더에 맞는 FQBN을 사용하세요.
FQBN = "arduino:avr:uno"
LEFT_POLARITY = 1   # 왼쪽 모터 방향이 반대라면 -1
RIGHT_POLARITY = 1  # 오른쪽 모터 방향이 반대라면 -1
