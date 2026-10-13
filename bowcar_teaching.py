"""Standalone teaching sketches without a HUSKYLENS target requirement."""
from pathlib import Path
import re
import shutil
import subprocess

from bowcar import UploadBowCar


def _integer(value, name, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError("{} must be an integer between {} and {}".format(name, low, high))
    return value


class _SortedSet(set):
    def __iter__(self):
        return iter(sorted(super().__iter__()))


class StandaloneBowCar(UploadBowCar):
    """Generate basic drive/sensor sketches; compiling never opens a port."""

    def __init__(self, fqbn=None, left_polarity=1, right_polarity=1):
        _integer(left_polarity, "left_polarity", -1, 1)
        _integer(right_polarity, "right_polarity", -1, 1)
        if left_polarity == 0 or right_polarity == 0:
            raise ValueError("Motor polarity must be 1 or -1")
        if fqbn is not None and (not isinstance(fqbn, str) or not fqbn.strip()):
            raise ValueError("fqbn must be a board identifier")
        super().__init__()
        self.fqbn = fqbn
        self.left_polarity, self.right_polarity = left_polarity, right_polarity
        for name in ("includes", "definitions", "globals", "declarations"):
            setattr(self, name, _SortedSet(getattr(self, name)))
        for pin in ("LM_DIR_PIN", "LM_PWM_PIN", "RM_DIR_PIN", "RM_PWM_PIN"):
            self._add_pin_mode(pin, "OUTPUT")
        self.setup_code += """  analogWrite(LM_PWM_PIN, 0);
  analogWrite(RM_PWM_PIN, 0);
  digitalWrite(LM_DIR_PIN, LOW);
  digitalWrite(RM_DIR_PIN, LOW);
"""

    def motor(self, left, right):
        _integer(left, "left", -255, 255)
        _integer(right, "right", -255, 255)
        super().motor(left * self.left_polarity, right * self.right_polarity)

    def begin_diagnostics(self):
        """Print BOOT and flash both LEDs three times once per restart."""
        if "Serial.println(F(\"BOOT\"))" in self.setup_code:
            return
        self._add_pin_mode("RED_LED_PIN", "OUTPUT")
        self._add_pin_mode("BLUE_LED_PIN", "OUTPUT")
        self.setup_code += """  Serial.println(F("BOOT"));
  for (int i = 0; i < 3; ++i) {
    digitalWrite(RED_LED_PIN, HIGH);
    digitalWrite(BLUE_LED_PIN, HIGH);
    delay(100);
    digitalWrite(RED_LED_PIN, LOW);
    digitalWrite(BLUE_LED_PIN, LOW);
    delay(100);
  }
"""

    def log(self, message):
        if not isinstance(message, str) or not re.fullmatch(r"[A-Za-z0-9_, =.-]{1,80}", message):
            raise ValueError("Use an ASCII diagnostic label")
        self.loop_code += '{}Serial.print(F("{},")); Serial.println(millis());\n'.format(
            self._get_indent(), message)

    def debug_values(self, fields, interval_ms=250):
        _integer(interval_ms, "interval_ms", 20, 60000)
        self.globals.add("unsigned long tc_lastDebug = 0;")
        lines = ["if (millis() - tc_lastDebug >= {}UL) {{".format(interval_ms),
                 "  tc_lastDebug = millis();", '  Serial.print(F("ms=")); Serial.print(millis());']
        for label, expression in fields:
            if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", label):
                raise ValueError("Use an ASCII field label")
            if not isinstance(expression, str) or not expression.strip() or any(c in expression for c in ";{}\n\r#"):
                raise ValueError("Use a single C++ expression")
            lines.append('  Serial.print(F(" {}=")); Serial.print({});'.format(label, expression))
        lines.extend(['  Serial.println(F(""));', "}"])
        indent = self._get_indent()
        self.loop_code += "".join(indent + line + "\n" for line in lines)

    def _ensure_distance_func(self):
        """Bound echo wait to 25 ms; callers still stop before each sample."""
        self._add_pin_mode("TRIG_PIN", "OUTPUT")
        self._add_pin_mode("ECHO_PIN", "INPUT")
        self.declarations.add("""long Distance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  unsigned long echo_us = pulseIn(ECHO_PIN, HIGH, 25000UL);
  return echo_us == 0 ? 0 : (long)(echo_us / 58UL);
}""")

    def export_sketch(self, directory="generated/basic_drive"):
        directory = Path(directory).expanduser().resolve()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", directory.name):
            raise ValueError("Use an ASCII sketch folder name")
        directory.mkdir(parents=True, exist_ok=True)
        ino = directory / (directory.name + ".ino")
        with ino.open("w", encoding="utf-8", newline="\n") as output:
            output.write(self.get_full_code())
        return ino

    def _run_cli(self, directory, port, fqbn, arduino_cli):
        board = fqbn or self.fqbn
        if not board:
            raise ValueError("Specify --fqbn matching your board/core/bootloader")
        executable = shutil.which(arduino_cli)
        if not executable:
            raise RuntimeError("arduino-cli was not found; see docs/INSTRUCTOR_GUIDE.md")
        ino = self.export_sketch(directory)
        command = [executable, "compile", "--fqbn", board]
        if port is not None:
            command.extend(["--upload", "--port", str(port)])
        command.append(str(ino.parent))
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if result.returncode:
            raise RuntimeError("arduino-cli failed:\n{}\n{}".format(result.stdout, result.stderr))
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())
        return ino

    def compile_code(self, directory="generated/basic_drive", fqbn=None, arduino_cli="arduino-cli"):
        return self._run_cli(directory, None, fqbn, arduino_cli)

    def upload_code(self, port=None, directory="generated/basic_drive", fqbn=None, arduino_cli="arduino-cli"):
        if not (fqbn or self.fqbn):
            raise ValueError("Specify --fqbn matching your board/core/bootloader")
        if port is None:
            from serial.tools import list_ports
            matches = [p.device for p in list_ports.comports()
                       if "arduino" in (p.description or "").lower() or "ch340" in (p.description or "").lower()]
            if len(matches) != 1:
                raise RuntimeError("Specify --port; found {} matching USB ports".format(len(matches)))
            port = matches[0]
        return self._run_cli(directory, port, fqbn, arduino_cli)
