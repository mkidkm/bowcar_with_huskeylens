"""색 인식 ID에 따라 바우카 네오픽셀 4개를 바꾸는 업로드 프로그램."""
import subprocess

from bowcar_huskylens import HuskyLensBowCar
from upload_settings import ROOT, PORT, FQBN, LEFT_POLARITY, RIGHT_POLARITY

BRIGHTNESS = 50  # 0~255


def build_program():
    car = HuskyLensBowCar(
        algorithm="color_recognition", target_id=None, selection="largest",
        fqbn=FQBN, left_polarity=LEFT_POLARITY, right_polarity=RIGHT_POLARITY,
    )
    car.begin_huskylens()  # 전원이 켜지면 setup()에서 Color Recognition으로 전환.
    car.motor(0, 0)
    car.neopixel_brightness(BRIGHTNESS)
    car.read_huskylens()
    found = car.has_target()
    color_id = car.get_target_id()

    with car.bif(f"{found} and {color_id} == 1"):
        car.neopixel_all(255, 0, 0)  # ID 1: 빨강
    with car.belif(f"{found} and {color_id} == 2"):
        car.neopixel_all(0, 255, 0)  # ID 2: 초록
    with car.belif(f"{found} and {color_id} == 3"):
        car.neopixel_all(0, 0, 255)  # ID 3: 파랑
    with car.belse():
        car.neopixel_clear()  # 미검출, 다른 ID, 통신 실패: 꺼짐

    car.debug_huskylens(250)
    car.delay(30)
    return car


if __name__ == "__main__":
    car = build_program()
    # 네오픽셀 사용에 필요한 Arduino 라이브러리를 확인/설치합니다.
    subprocess.run(["arduino-cli", "lib", "install", "Adafruit NeoPixel"], check=True)
    car.upload_code(port=PORT, fqbn=FQBN, directory=ROOT / "generated" / "color_neopixel")
