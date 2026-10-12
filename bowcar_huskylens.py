"""HUSKYLENS 1 I2C support for bowcar.UploadBowCar (tested against 1.3.4).

Python generates an Arduino sketch; returned sensor expressions run on the car.
This module does not open a serial port or flash a board at import time.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Union

from bowcar.upload import UploadBowCar

Code = Union[int, str]
ALGORITHMS = {
    "face_recognition": "ALGORITHM_FACE_RECOGNITION",
    "object_tracking": "ALGORITHM_OBJECT_TRACKING",
    "object_recognition": "ALGORITHM_OBJECT_RECOGNITION",
    "line_tracking": "ALGORITHM_LINE_TRACKING",
    "color_recognition": "ALGORITHM_COLOR_RECOGNITION",
    "tag_recognition": "ALGORITHM_TAG_RECOGNITION",
    "object_classification": "ALGORITHM_OBJECT_CLASSIFICATION",
}


class _SortedSet(set):
    def __iter__(self):
        return iter(sorted(super().__iter__()))


def _integer(value: int, name: str, low: int, high: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise ValueError("{} must be an integer between {} and {}".format(name, low, high))
    return value


def _expression(value: Code) -> str:
    if isinstance(value, int) and not isinstance(value, bool):
        # AVR long is 32 bits. Clamp constants before emitting them.
        return str(max(-255, min(255, value)))
    if isinstance(value, str) and value.strip() and not any(c in value for c in ";{}\n\r#"):
        return value.strip()
    raise ValueError("Use an integer or a single C++ speed expression.")


class HuskyLensBowCar(UploadBowCar):
    """Generate standalone BowCar programs using one HUSKYLENS on Wire/0x32.

    target_id=None selects learned IDs only. Blocks use the largest area by
    default; selection='lowest_id' gives smaller learned IDs priority.
    Positive motor speeds follow bowcar's original forward convention.
    fqbn must match the board/core/bootloader actually used on your car.
    """

    def __init__(
        self,
        algorithm: str = "object_tracking",
        target_id: Optional[int] = 1,
        selection: str = "largest",
        timeout_ms: int = 100,
        retry_ms: int = 1000,
        stale_ms: int = 300,
        left_polarity: int = 1,
        right_polarity: int = 1,
        fqbn: Optional[str] = None,
    ):
        if algorithm not in ALGORITHMS:
            raise ValueError("Unknown algorithm: {}".format(algorithm))
        if target_id is not None:
            _integer(target_id, "target_id", 1, 32767)
        if selection not in ("largest", "lowest_id"):
            raise ValueError("selection must be 'largest' or 'lowest_id'")
        _integer(timeout_ms, "timeout_ms", 20, 1000)
        _integer(retry_ms, "retry_ms", 100, 60000)
        _integer(stale_ms, "stale_ms", 50, 60000)
        if stale_ms <= timeout_ms:
            raise ValueError("stale_ms must be greater than timeout_ms")
        if not isinstance(left_polarity, int) or isinstance(left_polarity, bool) or left_polarity not in (-1, 1):
            raise ValueError("left_polarity must be 1 or -1")
        if not isinstance(right_polarity, int) or isinstance(right_polarity, bool) or right_polarity not in (-1, 1):
            raise ValueError("right_polarity must be 1 or -1")
        if fqbn is not None and (not isinstance(fqbn, str) or not fqbn.strip()):
            raise ValueError("fqbn must be a board identifier")

        super().__init__()
        for name in ("includes", "definitions", "globals", "declarations"):
            setattr(self, name, _SortedSet(getattr(self, name)))
        self.algorithm = algorithm
        self.fqbn = fqbn
        self.target_filter = target_id
        self.includes.update({'#include <Wire.h>', '#include "HUSKYLENS.h"'})
        self.globals.add("""// HUSKYLENS state: overwritten on every read; no stale coordinates.
HUSKYLENS bc_husky;
bool bc_connected = false;
bool bc_found = false;
bool bc_attempted = false;
unsigned long bc_lastAttempt = 0;
unsigned long bc_lastTarget = 0;
int bc_id = 0;
int bc_x = 0, bc_y = 0, bc_width = 0, bc_height = 0;
int bc_xOrigin = 0, bc_yOrigin = 0, bc_xTarget = 0, bc_yTarget = 0;
unsigned long bc_lastDebug = 0;
""")
        arrows = algorithm == "line_tracking"
        if target_id is None:
            request = "bc_husky.requestArrowsLearned()" if arrows else "bc_husky.requestBlocksLearned()"
        else:
            request = "bc_husky.{}({})".format("requestArrows" if arrows else "requestBlocks", target_id)
        command = "COMMAND_RETURN_ARROW" if arrows else "COMMAND_RETURN_BLOCK"
        id_check = "r.ID > 0" if target_id is None else "r.ID == {}".format(target_id)
        if arrows:
            valid = "r.xOrigin >= 0 && r.xOrigin <= 320 && r.yOrigin >= 0 && r.yOrigin <= 240 && r.xTarget >= 0 && r.xTarget <= 320 && r.yTarget >= 0 && r.yTarget <= 240"
            score = "0"
            save = """bc_xOrigin = r.xOrigin; bc_yOrigin = r.yOrigin;
      bc_xTarget = r.xTarget; bc_yTarget = r.yTarget;
      bc_x = r.xTarget; bc_y = r.yTarget;"""
        else:
            valid = "r.xCenter >= 0 && r.xCenter <= 320 && r.yCenter >= 0 && r.yCenter <= 240 && r.width > 0 && r.width <= 320 && r.height > 0 && r.height <= 240"
            score = "(long)r.width * (long)r.height"
            save = """bc_x = r.xCenter; bc_y = r.yCenter;
      bc_width = r.width; bc_height = r.height;"""
        choose = "!bc_found || r.ID < bc_id" if selection == "lowest_id" else "!bc_found || score > bestScore"
        helpers = r"""// Signed runtime motor speeds; stop whenever the camera target is invalid.
void bc_stop() {
  analogWrite(LM_PWM_PIN, 0);
  analogWrite(RM_PWM_PIN, 0);
}

void bc_motor(long left, long right) {
  if (!bc_connected || !bc_found || millis() - bc_lastTarget > @STALE@UL) {
    bc_stop();
    return;
  }
  if (left > 255) left = 255;
  if (left < -255) left = -255;
  if (right > 255) right = 255;
  if (right < -255) right = -255;
  left *= @LEFT@; right *= @RIGHT@;
  digitalWrite(LM_DIR_PIN, left < 0 ? HIGH : LOW);
  digitalWrite(RM_DIR_PIN, right < 0 ? HIGH : LOW);
  analogWrite(LM_PWM_PIN, left < 0 ? -left : left);
  analogWrite(RM_PWM_PIN, right < 0 ? -right : right);
}

void bc_clearTarget() {
  bc_found = false;
  bc_id = 0;
  bc_x = bc_y = bc_width = bc_height = 0;
  bc_xOrigin = bc_yOrigin = bc_xTarget = bc_yTarget = 0;
}

// Select the program's recognition mode at startup and after reconnection.
bool bc_connectCamera() {
  if (bc_connected) return true;
  bc_stop();
  if (bc_attempted && millis() - bc_lastAttempt < @RETRY@UL) return false;
  bc_attempted = true;
  bc_connected = bc_husky.begin(Wire);
  if (bc_connected) bc_connected = bc_husky.writeAlgorithm(@ALGORITHM@);
  bc_lastAttempt = millis();
  return bc_connected;
}

void bc_readTarget() {
  bc_clearTarget();
  if (!bc_connectCamera()) return;
  if (!@REQUEST@) {
    bc_connected = false;
    bc_lastAttempt = millis();
    bc_stop();
    return;
  }
  long bestScore = -1;
  while (bc_husky.available()) {
    HUSKYLENSResult r = bc_husky.read();
    if (r.command != @COMMAND@ || !(@ID_CHECK@) || !(@VALID@)) continue;
    long score = @SCORE@;
    if (@CHOOSE@) {
      bc_found = true;
      bc_id = r.ID;
      @SAVE@
      bestScore = score;
    }
  }
  if (bc_found) bc_lastTarget = millis();
  else bc_stop();
}

// A long generated delay also stops motors when the target becomes stale.
// This is cooperative checking, not an interrupt-based motor watchdog.
void bc_delay(unsigned long duration) {
  unsigned long started = millis();
  while (millis() - started < duration) {
    if (!bc_found || millis() - bc_lastTarget > @STALE@UL) bc_stop();
    delay(1);
  }
}

void bc_debug(unsigned long interval) {
  if (millis() - bc_lastDebug < interval) return;
  bc_lastDebug = millis();
  Serial.print(F("camera=")); Serial.print(bc_connected);
  Serial.print(F(" target=")); Serial.print(bc_found);
  Serial.print(F(" id=")); Serial.print(bc_id);
  Serial.print(F(" x=")); Serial.print(bc_x);
  Serial.print(F(" y=")); Serial.print(bc_y);
  Serial.print(F(" w=")); Serial.print(bc_width);
  Serial.print(F(" h=")); Serial.println(bc_height);
}
"""
        replacements = {
            "STALE": str(stale_ms), "LEFT": str(left_polarity), "RIGHT": str(right_polarity),
            "RETRY": str(retry_ms), "ALGORITHM": ALGORITHMS[algorithm], "REQUEST": request,
            "COMMAND": command, "ID_CHECK": id_check, "VALID": valid, "SCORE": score,
            "CHOOSE": choose, "SAVE": save,
        }
        for key, value in replacements.items():
            helpers = helpers.replace("@{}@".format(key), value)
        self.declarations.add(helpers)
        for pin in ("LM_DIR_PIN", "LM_PWM_PIN", "RM_DIR_PIN", "RM_PWM_PIN"):
            self._add_pin_mode(pin, "OUTPUT")
        self.setup_code += """  bc_stop();
  Wire.begin();
#if defined(WIRE_HAS_TIMEOUT)
  Wire.setWireTimeout(25000UL, true);
#endif
"""
        self.setup_code += "  bc_husky.setTimeOutDuration({}UL);\n".format(timeout_ms)

    def begin_huskylens(self) -> None:
        """Connect and select the configured recognition mode in Arduino setup()."""
        startup = "  bc_connectCamera();\n"
        if startup not in self.setup_code:
            self.setup_code += "  // Select {} before loop() starts.\n".format(self.algorithm)
            self.setup_code += startup

    def read_huskylens(self) -> None:
        """Append one camera poll to Arduino loop(). Call before acting on results."""
        self.loop_code += "{}bc_readTarget();\n".format(self._get_indent())

    def is_camera_connected(self) -> str:
        return "bc_connected"

    def has_target(self) -> str:
        return "bc_found"

    def get_target_id(self) -> str:
        return "bc_id"

    def get_target_x(self) -> str:
        """Block center x; for a line, arrow destination x (image width 320)."""
        return "bc_x"

    def get_target_y(self) -> str:
        return "bc_y"

    def get_target_width(self) -> str:
        return "bc_width"

    def get_target_height(self) -> str:
        return "bc_height"

    def get_arrow_x_origin(self) -> str:
        return "bc_xOrigin"

    def get_arrow_y_origin(self) -> str:
        return "bc_yOrigin"

    def get_arrow_x_target(self) -> str:
        return "bc_xTarget"

    def get_arrow_y_target(self) -> str:
        return "bc_yTarget"

    def motor(self, left: Code, right: Code) -> None:
        """Append guarded motor control. Accept literal speeds or C++ expressions."""
        self.loop_code += "{}bc_motor((long)({}), (long)({}));\n".format(
            self._get_indent(), _expression(left), _expression(right)
        )

    def delay(self, ms: int) -> None:
        _integer(ms, "ms", 0, 600000)
        self.loop_code += "{}bc_delay({}UL);\n".format(self._get_indent(), ms)

    def debug_huskylens(self, interval_ms: int = 250) -> None:
        _integer(interval_ms, "interval_ms", 20, 60000)
        self.loop_code += "{}bc_debug({}UL);\n".format(self._get_indent(), interval_ms)

    def export_sketch(self, directory: Union[str, Path] = "generated/bowcar_huskylens") -> Path:
        directory = Path(directory).expanduser().resolve()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,62}", directory.name):
            raise ValueError("Use an ASCII sketch folder name, for example follow_object.")
        directory.mkdir(parents=True, exist_ok=True)
        ino = directory / (directory.name + ".ino")
        ino.write_text(self.get_full_code(), encoding="utf-8")
        return ino

    def _run_cli(self, directory, port, fqbn, arduino_cli, library):
        board = fqbn or self.fqbn
        if not board:
            raise ValueError("Specify a fqbn matching your board/core/bootloader; see README.md.")
        executable = shutil.which(arduino_cli)
        if executable is None:
            raise RuntimeError("arduino-cli was not found. See README.md, or upload the .ino using Arduino IDE.")
        ino = self.export_sketch(directory)
        library = Path(library) if library is not None else Path(__file__).resolve().parent / "vendor" / "HUSKYLENS"
        if not (library / "HUSKYLENS.h").is_file():
            raise FileNotFoundError("HUSKYLENS library folder not found: {}".format(library))
        command = [executable, "compile", "--fqbn", board, "--library", str(library.resolve())]
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

    def compile_code(self, directory="generated/bowcar_huskylens", fqbn=None,
                     arduino_cli="arduino-cli", library=None) -> Path:
        """Compile without uploading; use the bundled official camera library."""
        return self._run_cli(directory, None, fqbn, arduino_cli, library)

    def upload_code(self, port=None, fqbn=None, directory="generated/bowcar_huskylens",
                    arduino_cli="arduino-cli", library=None) -> Path:
        """Compile and upload only when explicitly called; fail on ambiguous ports."""
        if port is None:
            from serial.tools import list_ports
            matches = [p.device for p in list_ports.comports()
                       if "arduino" in p.description.lower() or "ch340" in p.description.lower()]
            if len(matches) != 1:
                raise RuntimeError("Specify port='COM5' or port='/dev/ttyUSB0'; found {} matching ports.".format(len(matches)))
            port = matches[0]
        return self._run_cli(directory, port, fqbn, arduino_cli, library)
