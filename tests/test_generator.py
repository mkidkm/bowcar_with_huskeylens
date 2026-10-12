"""Software checks. A host protocol simulation does not replace hardware tests.

Run: python -m unittest discover -s tests -v
Python dependencies: requirements.txt. Host checks additionally require gcc/g++.
"""
import ast
import importlib
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "examples"))
from bowcar_huskylens import HuskyLensBowCar, ALGORITHMS

SETTINGS = {
    "connection_check": dict(target_id=None),
    "follow_object": dict(algorithm="object_tracking", target_id=1),
    "tag_actions": dict(algorithm="tag_recognition", target_id=None, selection="lowest_id"),
    "line_follow": dict(algorithm="line_tracking", target_id=1),
}


class GeneratorTests(unittest.TestCase):
    def test_invalid_configuration(self):
        for setting in ({"algorithm": "bad"}, {"target_id": 0}, {"target_id": True},
                        {"target_id": 32768}, {"timeout_ms": -1}, {"stale_ms": 100},
                        {"selection": "bad"}, {"left_polarity": 0}, {"left_polarity": 1.0}):
            with self.subTest(setting=setting), self.assertRaises(ValueError):
                HuskyLensBowCar(**setting)

    def test_default_generation_never_flashes(self):
        with patch("bowcar_huskylens.subprocess.run") as run:
            car = HuskyLensBowCar()
            with tempfile.TemporaryDirectory() as directory:
                ino = car.export_sketch(Path(directory) / "test_sketch")
                self.assertTrue(ino.is_file())
            run.assert_not_called()

    def test_upload_preserves_board_library_and_port_arguments(self):
        car = HuskyLensBowCar(fqbn="example:avr:custom")
        good = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as directory, \
             patch("bowcar_huskylens.shutil.which", return_value="/tool/arduino-cli"), \
             patch("bowcar_huskylens.subprocess.run", return_value=good) as run:
            car.upload_code(port="COM17", directory=Path(directory) / "test_sketch")
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--fqbn")+1], "example:avr:custom")
            self.assertEqual(command[command.index("--port")+1], "COM17")
            self.assertIn("--upload", command)
            self.assertTrue(Path(command[command.index("--library")+1], "HUSKYLENS.h").is_file())

    def test_upload_errors_are_visible(self):
        car = HuskyLensBowCar(fqbn="example:avr:custom")
        bad = subprocess.CompletedProcess([], 1, stdout="", stderr="compile failed")
        with tempfile.TemporaryDirectory() as directory, \
             patch("bowcar_huskylens.shutil.which", return_value="/tool/arduino-cli"), \
             patch("bowcar_huskylens.subprocess.run", return_value=bad), \
             self.assertRaisesRegex(RuntimeError, "compile failed"):
            car.compile_code(directory=Path(directory) / "test_sketch")

    def test_board_setting_must_be_explicit(self):
        car = HuskyLensBowCar()
        with patch("bowcar_huskylens.subprocess.run") as run, self.assertRaisesRegex(ValueError, "fqbn"):
            car.compile_code()
        run.assert_not_called()

    def test_motor_expressions_reject_statement_text(self):
        car = HuskyLensBowCar()
        for value in ("100; reset()", "", True, 1.5):
            with self.subTest(value=value), self.assertRaises(ValueError):
                car.motor(value, 100)

    def test_python_38_syntax(self):
        for path in list(ROOT.glob("*.py")) + list((ROOT / "examples").glob("*.py")):
            ast.parse(path.read_text(encoding="utf-8"), feature_version=(3, 8))


@unittest.skipUnless(shutil.which("g++") and shutil.which("gcc"), "gcc/g++ required for host simulation")
class HostProtocolTests(unittest.TestCase):
    def test_generated_examples_with_official_library(self):
        host = ROOT / "tests" / "host"
        vendor = ROOT / "vendor" / "HUSKYLENS"
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            core = temporary / "protocol.o"
            self._run(["gcc", "-std=gnu11", "-c", str(vendor / "HuskyLensProtocolCore.c"),
                       "-I" + str(vendor), "-o", str(core)])
            for number, (name, settings) in enumerate(SETTINGS.items(), 1):
                with self.subTest(example=name):
                    car = HuskyLensBowCar(**settings)
                    importlib.import_module(name).build(car)
                    ino = car.export_sketch(temporary / name)
                    executable = temporary / (name + "_test")
                    self._run(["g++", "-std=gnu++11", "-fpermissive", "-I" + str(host),
                               "-I" + str(vendor), '-DBC_SKETCH="' + ino.as_posix() + '"',
                               "-DBC_TEST=" + str(number), str(host / "runtime.cpp"), str(core),
                               "-o", str(executable)])
                    self._run([str(executable)])

    def test_startup_modes_and_connection_recovery(self):
        host = ROOT / "tests" / "host"
        vendor = ROOT / "vendor" / "HUSKYLENS"
        programs = (
            ("upload_color_neopixel", "ALGORITHM_COLOR_RECOGNITION", "0x24"),
            ("upload_face_follow", "ALGORITHM_FACE_RECOGNITION", "0x27"),
        )
        with tempfile.TemporaryDirectory() as temporary:
            temporary = Path(temporary)
            core = temporary / "protocol.o"
            self._run(["gcc", "-std=gnu11", "-c", str(vendor / "HuskyLensProtocolCore.c"),
                       "-I" + str(vendor), "-o", str(core)])
            for name, algorithm, request in programs:
                car = importlib.import_module(name).build_program()
                ino = car.export_sketch(temporary / name)
                executable = temporary / (name + "_startup_test")
                self._run(["g++", "-std=gnu++11", "-fpermissive", "-I" + str(host),
                           "-I" + str(vendor), '-DBC_SKETCH="' + ino.as_posix() + '"',
                           "-DBC_ALGORITHM=" + algorithm, "-DBC_REQUEST=" + request,
                           str(host / "startup_runtime.cpp"), str(core),
                           "-o", str(executable)])
                for scenario in ("ready", "camera_late", "ack_failed"):
                    with self.subTest(program=name, scenario=scenario):
                        self._run([str(executable), scenario])

    def _run(self, command):
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, "{}\n{}\n{}".format(command, result.stdout, result.stderr))


if __name__ == "__main__":
    unittest.main()
