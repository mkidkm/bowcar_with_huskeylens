"""Restart observation; idle is default, drive must be chosen explicitly."""
from _teaching import prepare, finish
import basic_drive


def build(car, mode="idle"):
    if mode == "drive":
        basic_drive.build(car)
        return
    if mode != "idle":
        raise ValueError("Choose idle or drive")
    car.begin_diagnostics()
    car.motor(0, 0)
    car.red("off")
    car.blue("on")
    car.log("IDLE")
    car.delay(500)
    car.blue("off")
    car.delay(500)


def options(parser):
    parser.add_argument("--mode", choices=("idle", "drive"), default="idle")


if __name__ == "__main__":
    car, args = prepare("power_check", "기본은 모터 정지: BOOT 반복과 주행시 리셋 여부 비교", options)
    build(car, args.mode)
    finish(car, args)
