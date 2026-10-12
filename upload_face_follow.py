"""인식한 얼굴의 x 좌표에 따라 바우카를 조향하는 업로드 프로그램."""
from bowcar_huskylens import HuskyLensBowCar
from upload_settings import ROOT, PORT, FQBN, LEFT_POLARITY, RIGHT_POLARITY

TARGET_FACE_ID = 1  # 학습한 얼굴 ID. None이면 학습한 얼굴 중 가장 큰 얼굴.
CENTER_X = 160
DEADBAND = 25
BASE_SPEED = 90
TURN_SPEED = 40
STOP_FACE_WIDTH = 120  # 얼굴 사각형 픽셀 너비. 실제 거리(cm)는 아닙니다.


def build_program():
    car = HuskyLensBowCar(
        algorithm="face_recognition", target_id=TARGET_FACE_ID,
        fqbn=FQBN, left_polarity=LEFT_POLARITY, right_polarity=RIGHT_POLARITY,
    )
    car.begin_huskylens()  # 전원이 켜지면 setup()에서 Face Recognition으로 전환.
    car.read_huskylens()
    found = car.has_target()
    x = car.get_target_x()
    width = car.get_target_width()

    with car.bif(f"not {found} or {width} >= {STOP_FACE_WIDTH}"):
        car.motor(0, 0)  # 얼굴 없음, 통신 실패, 가까워진 얼굴: 정지
        car.red("on")
        car.blue("off")
    with car.belse():
        car.red("off")
        car.blue("on")
        with car.bif(f"{x} < {CENTER_X - DEADBAND}"):
            car.motor(BASE_SPEED - TURN_SPEED, BASE_SPEED + TURN_SPEED)  # 왼쪽 조향
        with car.belif(f"{x} > {CENTER_X + DEADBAND}"):
            car.motor(BASE_SPEED + TURN_SPEED, BASE_SPEED - TURN_SPEED)  # 오른쪽 조향
        with car.belse():
            car.motor(BASE_SPEED, BASE_SPEED)  # 중앙: 전진

    car.debug_huskylens(250)
    car.delay(30)
    return car


if __name__ == "__main__":
    car = build_program()
    car.upload_code(port=PORT, fqbn=FQBN, directory=ROOT / "generated" / "face_follow")
