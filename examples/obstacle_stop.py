"""One bounded ultrasonic sample per loop; stop for missing/near echoes."""
from _teaching import prepare, finish

STOP_CM = 20
SPEED = 100


def build(car):
    car.begin_diagnostics()
    # Stop first: a missing echo must not keep the previous drive output active.
    car.motor(0, 0)
    car.set_value("long", "distance_cm", car.get_distance())
    with car.bif("distance_cm <= 0 or distance_cm <= {}".format(STOP_CM)):
        car.motor(0, 0)
        car.red("on")
        car.blue("off")
    with car.belse():
        car.motor(SPEED, SPEED)
        car.red("off")
        car.blue("on")
    car.debug_values([("distance_cm", "distance_cm")], 250)
    car.delay(100)


if __name__ == "__main__":
    car, args = prepare("obstacle_stop", "거리 20cm 이내/초음파 무응답이면 정지; 측정 전에도 모터 정지")
    build(car)
    finish(car, args)
