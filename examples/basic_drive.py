"""Forward/backward/turn/stop; pause before every direction change."""
from _teaching import prepare, finish

SPEED = 100
PAUSE_MS = 300


def build(car):
    car.begin_diagnostics()
    for name, left, right, duration, red, blue in (
        ("FORWARD", SPEED, SPEED, 1000, "on", "off"),
        ("BACKWARD", -SPEED, -SPEED, 1000, "off", "on"),
        ("LEFT", -SPEED, SPEED, 500, "on", "on"),
        ("RIGHT", SPEED, -SPEED, 500, "off", "off"),
    ):
        car.motor(0, 0)
        car.all_light("off")
        car.delay(PAUSE_MS)
        car.log("STEP," + name)
        car.motor(left, right)
        car.red(red)
        car.blue(blue)
        car.delay(duration)
        car.log("DONE," + name)
    car.motor(0, 0)
    car.all_light("off")
    car.log("STEP,STOP")
    car.delay(2000)
    car.log("DONE,STOP")


if __name__ == "__main__":
    car, args = prepare("basic_drive", "기본 주행: 방향 변경 전 300ms 정지, 3.7V 배터리 전원 ON 확인")
    build(car)
    finish(car, args)
