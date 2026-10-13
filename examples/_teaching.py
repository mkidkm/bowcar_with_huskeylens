"""Common options for examples that do not require HUSKYLENS."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bowcar_teaching import StandaloneBowCar


def prepare(name, description, configure=None):
    parser = argparse.ArgumentParser(description=description)
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--compile", action="store_true")
    actions.add_argument("--upload", action="store_true")
    parser.add_argument("--port", help="Upload USB port, for example COM11")
    parser.add_argument("--fqbn", help="Required for compile/upload, for example arduino:avr:uno")
    parser.add_argument("--output", type=Path, default=ROOT / "generated" / name)
    parser.add_argument("--reverse-left", action="store_true")
    parser.add_argument("--reverse-right", action="store_true")
    if configure:
        configure(parser)
    args = parser.parse_args()
    if (args.compile or args.upload) and not args.fqbn:
        parser.error("--compile/--upload requires --fqbn")
    if args.port and not args.upload:
        parser.error("--port is only used with --upload")
    car = StandaloneBowCar(fqbn=args.fqbn, left_polarity=-1 if args.reverse_left else 1,
                          right_polarity=-1 if args.reverse_right else 1)
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
