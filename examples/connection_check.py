"""I2C connection/recognition check; motors remain stopped."""
from _common import prepare, finish


def build(car):
    car.read_huskylens()
    car.motor(0, 0)
    car.debug_huskylens(250)
    with car.bif(car.is_camera_connected()):
        car.blue("on")
        car.red("off")
    with car.belse():
        car.blue("off")
        car.red("on")
    car.delay(30)


if __name__ == "__main__":
    car, args = prepare("connection_check", "허스키렌즈 I2C 연결 확인", target_id=None)
    build(car)
    finish(car, args)
