"""Standalone example contracts and generated C++ behavior; no device is opened."""
import ast
import contextlib
import importlib
import io
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))
from bowcar_teaching import StandaloneBowCar

EXAMPLES = ("basic_drive", "sensor_leds", "obstacle_stop", "power_check")


class StandaloneGeneratorTests(unittest.TestCase):
    def test_default_cli_only_exports_without_external_actions(self):
        with tempfile.TemporaryDirectory() as temporary:
            for name in EXAMPLES:
                with self.subTest(example=name):
                    output = Path(temporary) / name
                    argv = [name + ".py", "--output", str(output)]
                    with patch("sys.argv", argv), patch("subprocess.run") as run, \
                         patch("serial.tools.list_ports.comports") as ports, \
                         contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(str(ROOT / "examples" / (name + ".py")), run_name="__main__")
                    self.assertTrue((output / (name + ".ino")).is_file())
                    run.assert_not_called()
                    ports.assert_not_called()

    def test_cli_rejects_missing_board_and_unused_port(self):
        for arguments in (["--compile"], ["--upload"], ["--port", "COM11"]):
            with self.subTest(arguments=arguments), patch("sys.argv", ["basic_drive.py"] + arguments), \
                 patch("subprocess.run") as run, patch("serial.tools.list_ports.comports") as ports, \
                 contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                runpy.run_path(str(ROOT / "examples" / "basic_drive.py"), run_name="__main__")
            self.assertEqual(error.exception.code, 2)
            run.assert_not_called()
            ports.assert_not_called()

    def test_compile_upload_arguments_and_error_output(self):
        car = StandaloneBowCar(fqbn="example:avr:configured")
        good = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as temporary, \
             patch("bowcar_teaching.shutil.which", return_value="/tool/arduino-cli"), \
             patch("bowcar_teaching.subprocess.run", return_value=good) as run, \
             patch("serial.tools.list_ports.comports") as ports:
            directory = Path(temporary) / "standalone"
            car.compile_code(directory=directory, fqbn="example:avr:override")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--fqbn") + 1], "example:avr:override")
            self.assertNotIn("--upload", command)
            self.assertNotIn("--port", command)
            car.upload_code(port="COM11", directory=directory)
            command = run.call_args.args[0]
            self.assertIn("--upload", command)
            self.assertEqual(command[command.index("--port") + 1], "COM11")
            self.assertEqual(command[command.index("--fqbn") + 1], "example:avr:configured")
            self.assertNotIn("--library", command)
            ports.assert_not_called()
            run.return_value = subprocess.CompletedProcess([], 1, stdout="build detail", stderr="compile failed")
            with self.assertRaisesRegex(RuntimeError, "build detail[\\s\\S]*compile failed"):
                car.compile_code(directory=directory)

    def test_upload_board_requirement_and_automatic_port_ambiguity(self):
        with patch("subprocess.run") as run, patch("serial.tools.list_ports.comports") as ports:
            for operation in (StandaloneBowCar().compile_code, StandaloneBowCar().upload_code):
                with self.assertRaisesRegex(ValueError, "fqbn"):
                    operation()
            run.assert_not_called()
            ports.assert_not_called()
        recognized = SimpleNamespace(device="COM17", description="USB CH340")
        unrelated = SimpleNamespace(device="COM18", description=None)
        another = SimpleNamespace(device="COM19", description="Arduino USB")
        good = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as temporary, \
             patch("bowcar_teaching.shutil.which", return_value="/tool/arduino-cli"), \
             patch("bowcar_teaching.subprocess.run", return_value=good) as run, \
             patch("serial.tools.list_ports.comports") as ports:
            car = StandaloneBowCar(fqbn="example:avr:configured")
            for candidates, count in (([unrelated], 0), ([recognized, another], 2)):
                ports.return_value = candidates
                with self.subTest(matches=count), self.assertRaisesRegex(RuntimeError, "found {}".format(count)):
                    car.upload_code(directory=Path(temporary) / "automatic")
                run.assert_not_called()
            ports.return_value = [unrelated, recognized]
            car.upload_code(directory=Path(temporary) / "automatic")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--port") + 1], "COM17")

    def test_motor_range_and_polarity_validation(self):
        for setting in ({"left_polarity": 0}, {"right_polarity": 2},
                        {"left_polarity": True}, {"right_polarity": 1.0}):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                StandaloneBowCar(**setting)
        car = StandaloneBowCar(left_polarity=-1, right_polarity=1)
        for left, right in ((256, 0), (-256, 0), (True, 0), (0, 1.0), (0, "100")):
            previous = car.loop_code
            with self.subTest(left=left, right=right), self.assertRaises(ValueError):
                car.motor(left, right)
            self.assertEqual(car.loop_code, previous)
        car.motor(-255, 255)

    def test_python_38_syntax(self):
        paths = [ROOT / "bowcar_teaching.py", Path(__file__)]
        paths.extend(ROOT / "examples" / (name + ".py") for name in EXAMPLES + ("_teaching",))
        for path in paths:
            ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 8))


@unittest.skipUnless(shutil.which("g++"), "g++ required for standalone host simulation")
class StandaloneHostTests(unittest.TestCase):
    def test_generated_teaching_programs(self):
        programs = (
            ("basic_drive", {}, 1, 1, 1), ("basic_drive", {}, 1, -1, 1),
            ("sensor_leds", {"sensor": "button"}, 2, 1, 1),
            ("sensor_leds", {"sensor": "light"}, 3, 1, 1),
            ("sensor_leds", {"sensor": "sound"}, 4, 1, 1),
            ("sensor_leds", {"sensor": "line"}, 5, 1, 1),
            ("obstacle_stop", {}, 6, 1, 1), ("power_check", {}, 7, 1, 1),
            ("power_check", {"mode": "drive"}, 1, 1, 1),
        )
        host = ROOT / "tests" / "host_standalone"
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            for number, (name, options, case, left, right) in enumerate(programs):
                with self.subTest(example=name, options=options, polarity=(left, right)):
                    module = importlib.import_module(name)
                    car = StandaloneBowCar(left_polarity=left, right_polarity=right)
                    module.build(car, **options)
                    ino = car.export_sketch(temporary / (name + "_" + str(number)))
                    executable = temporary / (name + "_" + str(number) + "_host")
                    definitions = ["-DTC_CASE=" + str(case), "-DTC_LEFT=" + str(left), "-DTC_RIGHT=" + str(right)]
                    if name == "basic_drive" or options.get("mode") == "drive":
                        definitions.append("-DTC_SPEED=" + str(importlib.import_module("basic_drive").SPEED))
                    if name == "sensor_leds" and options["sensor"] != "button":
                        definitions.append("-DTC_THRESHOLD=" + str(getattr(module, options["sensor"].upper() + "_THRESHOLD")))
                    if name == "obstacle_stop":
                        definitions.append("-DTC_STOP_CM=" + str(module.STOP_CM))
                    command = ["g++", "-std=c++11", "-I" + str(host), '-DTC_SKETCH="' + ino.as_posix() + '"']
                    self._run(command + definitions + [str(host / "runtime.cpp"), "-o", str(executable)])
                    self._run([str(executable)])

    def _run(self, command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, "{}\n{}\n{}".format(command, result.stdout, result.stderr))


if __name__ == "__main__":
    unittest.main()
