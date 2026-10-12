"""Shared example options. Generating a sketch is the default action."""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bowcar_huskylens import HuskyLensBowCar


def prepare(name, description, **settings):
    parser = argparse.ArgumentParser(description=description)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--compile", action="store_true", help="Compile using arduino-cli")
    actions.add_argument("--upload", action="store_true", help="Compile and upload using arduino-cli")
    parser.add_argument("--port", help="USB serial port, for example COM5 or /dev/ttyUSB0")
    parser.add_argument("--fqbn", help="Required for compile/upload: use the board/core/bootloader setting known to work on your car")
    parser.add_argument("--output", type=Path, default=ROOT / "generated" / name)
    parser.add_argument("--reverse-left", action="store_true", help="Invert left motor polarity")
    parser.add_argument("--reverse-right", action="store_true", help="Invert right motor polarity")
    args = parser.parse_args()
    car = HuskyLensBowCar(fqbn=args.fqbn, left_polarity=-1 if args.reverse_left else 1,
                         right_polarity=-1 if args.reverse_right else 1, **settings)
    return car, args


def finish(car, args):
    try:
        if args.upload:
            ino = car.upload_code(port=args.port, directory=args.output)
        elif args.compile:
            ino = car.compile_code(directory=args.output)
        else:
            ino = car.export_sketch(args.output)
    except (RuntimeError, ValueError, OSError) as error:
        raise SystemExit(str(error))
    print("Sketch: {}".format(ino))
