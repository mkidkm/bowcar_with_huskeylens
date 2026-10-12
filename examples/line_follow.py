"""Follow a learned line arrow using runtime motor speed expressions."""
from _common import prepare, finish

BASE_SPEED = 90
CENTER_X = 160
GAIN_NUMERATOR = 1
GAIN_DENOMINATOR = 2


def build(car):
    car.read_huskylens()
    correction = "({} - {}) * {} / {}".format(
        car.get_arrow_x_target(), CENTER_X, GAIN_NUMERATOR, GAIN_DENOMINATOR)
    with car.bif(car.has_target()):
        car.motor("{} + ({})".format(BASE_SPEED, correction),
                  "{} - ({})".format(BASE_SPEED, correction))
        car.blue("on")
        car.red("off")
    with car.belse():
        car.motor(0, 0)
        car.blue("off")
        car.red("on")
    car.delay(20)


if __name__ == "__main__":
    car, args = prepare("line_follow", "학습한 선 ID 1 추종", algorithm="line_tracking", target_id=1)
    build(car)
    finish(car, args)
