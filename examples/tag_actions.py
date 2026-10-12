"""Learned tag IDs: 1 stop, 2 left, 3 right, 4 forward. Smaller ID wins."""
from _common import prepare, finish

SPEED = 90


def build(car):
    car.read_huskylens()
    with car.bif("{} and {} == 2".format(car.has_target(), car.get_target_id())):
        car.motor(-SPEED, SPEED)
        car.red("off")
        car.blue("on")
    with car.belif("{} and {} == 3".format(car.has_target(), car.get_target_id())):
        car.motor(SPEED, -SPEED)
        car.red("off")
        car.blue("on")
    with car.belif("{} and {} == 4".format(car.has_target(), car.get_target_id())):
        car.motor(SPEED, SPEED)
        car.red("off")
        car.blue("on")
    with car.belse():
        # Includes ID 1, unknown IDs, no learned tag, and communication failure.
        car.motor(0, 0)
        car.red("on")
        car.blue("off")
    car.delay(30)


if __name__ == "__main__":
    car, args = prepare("tag_actions", "학습한 태그 ID로 동작 선택", algorithm="tag_recognition",
                        target_id=None, selection="lowest_id")
    build(car)
    finish(car, args)
