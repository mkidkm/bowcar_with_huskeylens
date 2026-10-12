"""Follow learned object ID 1 slowly; stop on loss or a large image box."""
from _common import prepare, finish

BASE_SPEED = 100
TURN_SPEED = 45
CENTER_X = 160
DEADBAND = 25
STOP_WIDTH = 100  # Image pixels, not a calibrated distance in cm.


def build(car):
    car.read_huskylens()
    x = car.get_target_x()
    with car.bif("{} and {} < {}".format(car.has_target(), car.get_target_width(), STOP_WIDTH)):
        car.blue("on")
        car.red("off")
        with car.bif("{} < {}".format(x, CENTER_X - DEADBAND)):
            car.motor(BASE_SPEED - TURN_SPEED, BASE_SPEED + TURN_SPEED)
        with car.belif("{} > {}".format(x, CENTER_X + DEADBAND)):
            car.motor(BASE_SPEED + TURN_SPEED, BASE_SPEED - TURN_SPEED)
        with car.belse():
            car.motor(BASE_SPEED, BASE_SPEED)
    with car.belse():
        car.motor(0, 0)
        car.blue("off")
        car.red("on")
    car.delay(30)


if __name__ == "__main__":
    car, args = prepare("follow_object", "학습한 물체 ID 1 추종", algorithm="object_tracking", target_id=1)
    build(car)
    finish(car, args)
