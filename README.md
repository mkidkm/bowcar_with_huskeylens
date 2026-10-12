# 바우카 + 허스키렌즈

바우카에서 **HUSKYLENS 1(SEN0305)**의 인식 결과를 I2C로 읽어 LED, 네오픽셀, 모터를 제어하는 Python 확장입니다. `bowcar.UploadBowCar`를 상속한 `HuskyLensBowCar`로 Arduino 프로그램을 만들고 컴파일·업로드합니다. 업로드한 프로그램은 바우카 MCU의 `setup()`과 `loop()`에서 독립적으로 실행됩니다.

공개 저장소는 **[mkidkm/bowcar_with_huskeylens](https://github.com/mkidkm/bowcar_with_huskeylens)**입니다. 다음 명령으로 받을 수 있습니다.

```powershell
git clone https://github.com/mkidkm/bowcar_with_huskeylens.git
cd bowcar_with_huskeylens
```

## 들어 있는 파일

| 파일·폴더 | 내용 |
|---|---|
| [bowcar_huskylens.py](bowcar_huskylens.py) | 허스키렌즈 I2C 연결, 모드 설정, 대상 선택, 코드 생성·업로드 확장 |
| [upload_settings.py](upload_settings.py) | USB 포트, 보드 설정, 모터 극성 |
| [upload_color_neopixel.py](upload_color_neopixel.py) | 색 ID별 네오픽셀 색 변경, 모터 정지 유지 |
| [upload_face_follow.py](upload_face_follow.py) | 학습한 얼굴의 x 좌표에 따른 조향·전진 |
| [examples/](examples/) | 연결 확인, 물체 추종, 태그 동작, 선 추종 예제 |
| [generated/](generated/) | Python으로 생성한 Arduino `.ino` 스케치 |
| [tests/](tests/) | Python 코드 생성 검사와 호스트 C/C++ 모의 시험 |
| [vendor/HUSKYLENS/](vendor/HUSKYLENS/) | Arduino CLI에 전달하는 제조사 원본 라이브러리 |
| [HUSKYLENS_library.zip](HUSKYLENS_library.zip) | Arduino IDE에서 설치할 제조사 라이브러리 |
| [VERIFICATION.txt](VERIFICATION.txt) | 검증 환경, 결과, 실물 확인 범위 |
| [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) | 외부 의존성과 제조사 라이브러리 출처·라이선스 |
| [docs/README_color_face.txt](docs/README_color_face.txt) | 색·얼굴 업로드 프로그램의 기존 상세 안내 |

## 설치와 보드 설정

Python 의존성은 외부 패키지 **`bowcar==1.3.4`**입니다. 이 저장소에서 `bowcar` 자체를 배포하지 않습니다. 저장소 폴더에서 설치합니다.

```powershell
python -m pip install -r requirements.txt
```

[Arduino CLI를 설치](https://docs.arduino.cc/arduino-cli/installation/)하고 `arduino-cli` 명령을 실행할 수 있도록 PATH에 등록합니다. Arduino AVR Boards 코어도 준비합니다.

```powershell
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli core list
```

`pip install`은 Python 의존성을 설치합니다. Arduino CLI와 보드 코어는 별도 설치가 필요합니다. 설치 흐름은 [Arduino CLI 공식 안내](https://docs.arduino.cc/arduino-cli/getting-started/)를 참고하세요.

색·얼굴 업로드 프로그램은 `upload_settings.py`의 다음 설정을 사용합니다.

```python
PORT = None
FQBN = "arduino:avr:uno"
LEFT_POLARITY = 1
RIGHT_POLARITY = 1
```

- `PORT=None`: Arduino/CH340 USB 포트를 자동 탐색합니다. 대상이 하나이면 선택하며, 없거나 여러 개이면 직접 지정해야 합니다. Windows의 지정 예시는 `PORT="COM11"`입니다. 연결할 때마다 포트 번호가 달라질 수 있습니다. macOS/Linux에서는 실제 `/dev/...` 포트를 사용합니다.
- `FQBN="arduino:avr:uno"`: **ATmega328P / Arduino UNO 호환 보드·부트로더** 기준입니다. 이 설정에는 **MiniCore가 필요하지 않습니다.** 실제 칩·클럭·부트로더에 맞는 보드 설정을 사용하세요. 칩 이름만으로 UNO 설정 호환 여부를 확정할 수는 없습니다.
- `LEFT_POLARITY`, `RIGHT_POLARITY`: 해당 바퀴가 반대로 돌면 `-1`로 변경합니다.

포트 목록을 확인하려면 다음 명령을 사용합니다.

```powershell
arduino-cli board list
```

## 허스키렌즈 I2C 연결

허스키렌즈에서 **General Settings → Protocol Type → I2C**를 선택합니다. 이 확장은 `Wire`와 기본 I2C 주소 `0x32`를 사용합니다.

| 허스키렌즈 단자 | ATmega328P/UNO 쪽 연결 |
|---|---|
| `T` / SDA | `A4` / `PC4` / SDA |
| `R` / SCL | `A5` / `PC5` / SCL |
| `+` | 카메라 전원, 공급 범위 3.3~5.0V |
| `-` | GND, 바우카와 공통 접지 |

`+`는 전원 단자입니다. GPIO 신호선과 구분해서 연결하세요. 전원 규격과 I2C 설정은 [DFRobot 제품 사양](https://www.dfrobot.com/product-1922.html)과 [I2C 연결 안내](https://wiki.dfrobot.com/sen0305/docs/22766)를 참고하세요.

기존 J5 회로도에서 빨간 수정이 반영된 보드라면 SDA는 J5 8번, SCL은 J5 6번입니다. 수정 전 도면은 반대로 표기되어 있으므로 **실물에서 A4/SDA와 A5/SCL 연결을 확인**해야 합니다. 이 저장소의 컴파일 결과로 J5 배선, 전원, 실제 GPIO 동작을 검증한 것은 아닙니다.

## 바로 업로드하는 프로그램

아래 두 파일은 **실행하면 컴파일 후 보드에 업로드합니다.** 서로 다른 인식 모드를 사용하는 별도 프로그램이므로 원하는 프로그램 하나를 업로드하세요. 전원이 켜지면 카메라 연결과 지정 모드 전환을 먼저 시도합니다. 연결 또는 모드 설정 응답에 실패하면 모터를 정지한 상태로 반복 실행 중 다시 시도합니다.

### 색 인식 → 네오픽셀

허스키렌즈의 Color Recognition 모드에서 Learn Multiple을 켜고 빨강, 초록, 파랑을 순서대로 학습합니다. 화면에 빨강 `Color ID1`, 초록 `Color ID2`, 파랑 `Color ID3`이 표시되는지 확인합니다. **학습 ID는 색 자체에 고정된 번호가 아니라 학습 순서의 번호**입니다.

```powershell
python upload_color_neopixel.py
```

시작 시 **Color Recognition**으로 전환합니다. 기본 네오픽셀 데이터 핀 `D9`, LED 4개, GRB 형식을 사용합니다.

| 인식 결과 | 네오픽셀 4개 |
|---|---|
| ID1 | 빨강 |
| ID2 | 초록 |
| ID3 | 파랑 |
| 다른 ID, 대상 없음, 통신 실패 | 꺼짐 |

여러 색이 동시에 검출되면 사각형 면적이 가장 큰 학습 대상을 선택합니다. 미학습 ID0은 제외합니다. 모터는 항상 정지합니다. 밝기는 파일 위쪽의 `BRIGHTNESS`로 설정하며 기본값은 50, 범위는 0~255입니다.

이 파일은 업로드 전에 `arduino-cli lib install "Adafruit NeoPixel"`을 실행하여 라이브러리를 준비합니다. 처음 설치할 때는 인터넷 연결이 필요할 수 있습니다.

### 얼굴 좌표 → 바우카 추종

Face Recognition 모드에서 따라갈 얼굴을 먼저 학습하고 화면에 `Face ID1`이 표시되는지 확인합니다. **처음 시험할 때는 바퀴를 바닥에서 띄우고 방향을 확인**하세요.

```powershell
python upload_face_follow.py
```

시작 시 **Face Recognition**으로 전환합니다. 기본값 `TARGET_FACE_ID=1`은 학습한 얼굴 ID1만 선택합니다. `None`으로 바꾸면 학습된 얼굴 중 사각형 면적이 가장 큰 얼굴을 선택하며 미학습 ID0은 제외합니다.

| 얼굴 중심 x | 왼쪽·오른쪽 모터 PWM | 동작 |
|---|---|---|
| `x < 135` | 50, 130 | 왼쪽 조향 |
| `135 ≤ x ≤ 185` | 90, 90 | 전진 |
| `x > 185` | 130, 50 | 오른쪽 조향 |

얼굴이 사라지거나 인식 요청이 실패하면 정지합니다. 얼굴 너비가 `STOP_FACE_WIDTH`(기본 120픽셀) 이상일 때도 정지합니다. **픽셀 너비는 거리(cm)가 아니므로** 촬영 조건에 맞게 조정하세요.

파일 위쪽에서 `CENTER_X`, `DEADBAND`, `BASE_SPEED`, `TURN_SPEED`, `STOP_FACE_WIDTH`를 변경할 수 있습니다. 기본값은 화면 중앙 x=160, 허용 범위 ±25, 속도 90, 조향 속도 차이 40입니다. 빨강·파랑 LED와 시리얼 로그로 상태를 표시합니다.

## 기본 예제 4개

`examples/`의 예제는 **옵션 없이 실행하면 `.ino` 생성만 수행**합니다. 색·얼굴 업로드 파일과 실행 방식이 다릅니다.

| 예제 | 인식 모드와 동작 |
|---|---|
| `connection_check.py` | Object Tracking 모드의 연결·인식 상태 출력, 모터 정지 유지 |
| `follow_object.py` | Object Tracking, 학습 ID1 추종. 대상 소실·너비 기준에서 정지 |
| `tag_actions.py` | Tag Recognition, ID1 정지·ID2 왼쪽·ID3 오른쪽·ID4 전진. 여러 태그 중 작은 ID 우선 |
| `line_follow.py` | Line Tracking, 학습 ID1 화살표 끝점으로 조향 |

```powershell
# 스케치 생성만
python examples/connection_check.py

# 컴파일만
python examples/connection_check.py --compile --fqbn arduino:avr:uno

# 컴파일·업로드, 포트 자동 탐색
python examples/connection_check.py --upload --fqbn arduino:avr:uno

# 포트 직접 지정
python examples/connection_check.py --upload --fqbn arduino:avr:uno --port COM11
```

다른 예제도 파일명만 바꾸면 같은 옵션을 사용할 수 있습니다. `--compile`·`--upload`에는 실제 보드에 맞는 `--fqbn`을 지정해야 합니다. 이 예제들은 루트의 `upload_settings.py`를 자동으로 읽지 않습니다. `--reverse-left`·`--reverse-right`로 각 모터 극성을 반전할 수 있고 `--output`으로 생성 폴더를 지정할 수 있습니다.

## 허스키렌즈 함수 19개

아래 함수는 `HuskyLensBowCar`의 Python 인터페이스입니다. Python이 PC에서 코드를 생성하고, 센서 통신과 제어는 업로드된 Arduino 프로그램에서 실행됩니다.

| 함수 | 기능 |
|---|---|
| `begin_huskylens()` | `setup()`에 연결·지정 모드 전환 코드를 추가. 생성자 다음에 한 번 호출. 실패하면 `loop()`에서 재시도 |
| `read_huskylens()` | `loop()`에 인식 결과 갱신 코드를 추가. 결과를 사용하는 코드보다 앞에 호출 |
| `is_camera_connected()` | 연결·모드 설정 및 최근 통신 상태 표현식. 새 통신 요청은 보내지 않음 |
| `has_target()` | 설정한 학습 ID·좌표 조건에 맞는 대상이 검출됐는지 확인 |
| `get_target_id()` | 선택한 대상의 학습 ID. 색 인식에서도 RGB 값이 아닌 ID |
| `get_target_x()` | 사각형 중심 x. 선 추적에서는 화살표 끝점 x |
| `get_target_y()` | 사각형 중심 y. 선 추적에서는 화살표 끝점 y |
| `get_target_width()` | 사각형 너비, 단위는 픽셀. 선 추적에서는 사용하지 않음 |
| `get_target_height()` | 사각형 높이, 단위는 픽셀. 선 추적에서는 사용하지 않음 |
| `get_arrow_x_origin()` | 선 추적 화살표 시작점 x |
| `get_arrow_y_origin()` | 선 추적 화살표 시작점 y |
| `get_arrow_x_target()` | 선 추적 화살표 끝점 x |
| `get_arrow_y_target()` | 선 추적 화살표 끝점 y |
| `debug_huskylens(interval_ms=250)` | 지정 주기로 camera/target/id/x/y/w/h 출력. 기본 250ms, 9600 baud |
| `motor(left, right)` | 대상 유효성을 검사하며 모터 제어. 속도 −255~255, 정수 또는 하나의 C++ 속도 표현식 |
| `delay(ms)` | 지연 코드를 추가하고 지연 중 오래된 결과에 대한 모터 정지 검사 |
| `export_sketch(directory)` | 지정 폴더에 같은 이름의 `.ino`를 생성하고 경로 반환 |
| `compile_code(directory=..., fqbn=...)` | Arduino CLI로 컴파일만 수행하고 `.ino` 경로 반환 |
| `upload_code(port=None, directory=..., fqbn=...)` | 컴파일 후 업로드하고 `.ino` 경로 반환. `port=None`이면 자동 탐색 |

대상 없음·요청 실패 시 대상 ID와 좌표·크기는 0으로 초기화됩니다. `motor()`는 대상이 없거나 결과가 오래되었으면 정지합니다. 이 검사는 MCU가 다른 함수에서 멈춘 상황까지 감시하는 하드웨어 워치독은 아닙니다.

`export_sketch()`의 마지막 폴더 이름은 `color_id_example`처럼 영문·숫자·밑줄을 사용하고 영문 또는 밑줄로 시작해야 합니다. 예: `generated/color_id_example/color_id_example.ino`.

### 인식 모드와 대상 설정

생성자의 `algorithm`으로 모드를 지정하고 `begin_huskylens()`로 시작 시 적용합니다. 실행 중 모드를 바꾸는 별도의 Python 함수는 현재 제공하지 않습니다.

| `algorithm` 값 | 허스키렌즈 모드 |
|---|---|
| `face_recognition` | Face Recognition / 얼굴 인식 |
| `color_recognition` | Color Recognition / 색 인식 |
| `object_tracking` | Object Tracking / 물체 추적 |
| `object_recognition` | Object Recognition / 물체 인식 |
| `line_tracking` | Line Tracking / 선 추적 |
| `tag_recognition` | Tag Recognition / 태그 인식 |
| `object_classification` | Object Classification / 물체 분류 |

| 생성자 설정 | 의미 |
|---|---|
| `target_id=1` | 학습 ID1만 선택. 다른 양의 학습 ID도 지정 가능 |
| `target_id=None` | 학습된 ID 전체에서 선택. 미학습 ID0 제외 |
| `selection="largest"` | 기본값. 가장 큰 사각형 선택 |
| `selection="lowest_id"` | 작은 학습 ID 우선 선택 |
| `timeout_ms=100` | 제조사 라이브러리 응답 대기 시간. 요청 전체가 100ms 안에 끝난다는 뜻은 아님 |
| `retry_ms=1000` | 연결·모드 설정 실패 후 재시도 간격 |
| `stale_ms=300` | `motor()`·`delay()`의 오래된 결과 판정 기준. `timeout_ms`보다 커야 함 |
| `left_polarity=1`, `right_polarity=1` | 각 모터 방향. 1 또는 −1 |
| `fqbn=...` | 실제 보드·코어·부트로더 설정. 색·얼굴 업로드 예제는 `arduino:avr:uno` 사용 |

### 표현식 문자열 사용

결과 함수는 Python 숫자나 `bool`이 아니라 **MCU에서 평가하는 C++ 표현식 문자열**을 반환합니다. 일반 Python `if` 대신 `with car.bif(...)`, `car.belif(...)`, `car.belse()`를 사용하세요.

```python
car.read_huskylens()
with car.bif(car.has_target()):
    car.blue("on")
with car.belse():
    car.blue("off")
```

`print(car.get_target_x())`는 실제 센서 좌표를 읽는 방법이 아닙니다. 실제 결과 출력에는 `debug_huskylens()`와 시리얼 모니터를 사용합니다.

## 간단한 사용 예제

아래 파일을 저장소 루트에 만들어 실행하면 `.ino` 생성만 수행합니다. 두 프로그램 모두 모터를 정지합니다. 먼저 허스키렌즈의 I2C 설정과 색·얼굴 학습을 완료하세요.

### 색 ID1이면 네오픽셀을 빨강으로 켜기

`color_id_example.py`:

```python
from bowcar_huskylens import HuskyLensBowCar
from upload_settings import ROOT, FQBN

car = HuskyLensBowCar(
    algorithm="color_recognition", target_id=None, fqbn=FQBN,
)
car.begin_huskylens()
car.motor(0, 0)
car.neopixel_brightness(50)
car.read_huskylens()

with car.bif(f"{car.has_target()} and {car.get_target_id()} == 1"):
    car.neopixel_all(255, 0, 0)
with car.belse():
    car.neopixel_clear()

car.debug_huskylens(250)
car.delay(30)
output_dir = ROOT / "generated" / "color_id_example"
ino = car.export_sketch(output_dir)
print(ino)
```

```powershell
python color_id_example.py
```

생성 파일은 `generated/color_id_example/color_id_example.ino`입니다.
시작 시 Color Recognition으로 전환합니다. 학습된 색 중 가장 큰 대상이 ID1이면 빨강, 다른 ID·미검출·통신 실패이면 꺼집니다. `neopixel_brightness()`·`neopixel_all()`·`neopixel_clear()`는 기존 `bowcar`의 네오픽셀 함수입니다. 컴파일·업로드 전에는 다음 라이브러리가 필요합니다.

```powershell
arduino-cli lib install "Adafruit NeoPixel"
```

### 얼굴 ID1이면 파랑 LED 켜기

`face_detect_example.py`:

```python
from bowcar_huskylens import HuskyLensBowCar
from upload_settings import ROOT, FQBN

car = HuskyLensBowCar(
    algorithm="face_recognition", target_id=1, fqbn=FQBN,
)
car.begin_huskylens()
car.motor(0, 0)
car.read_huskylens()

with car.bif(car.has_target()):
    car.blue("on")
    car.red("off")
with car.belse():
    car.blue("off")
    car.red("on")

car.debug_huskylens(250)
car.delay(30)
output_dir = ROOT / "generated" / "face_detect_example"
ino = car.export_sketch(output_dir)
print(ino)
```

```powershell
python face_detect_example.py
```

생성 파일은 `generated/face_detect_example/face_detect_example.ino`입니다. 시작 시 Face Recognition으로 전환합니다. 얼굴 ID1이 검출되면 파랑 LED, 미검출·통신 실패이면 빨강 LED가 켜집니다. `blue()`·`red()`는 기존 `bowcar`의 LED 함수입니다. 얼굴을 따라 주행하려면 `upload_face_follow.py`를 사용하세요.

### 직접 만든 예제 컴파일·업로드

예제의 `ino = car.export_sketch(output_dir)` 한 줄을 다음 코드로 바꾸면 컴파일만 수행합니다.

```python
ino = car.compile_code(directory=output_dir)
```

컴파일·업로드하려면 다음과 같이 바꿉니다. `PORT=None`이면 자동 탐색하며, `upload_settings.py`에 `PORT="COM11"`처럼 직접 지정할 수도 있습니다.

```python
from upload_settings import PORT
ino = car.upload_code(port=PORT, directory=output_dir)
```

## Arduino IDE에서 업로드

Python 없이 `generated/`의 `.ino`를 Arduino IDE에서 열어 업로드할 수도 있습니다.

1. **스케치 → 라이브러리 포함하기 → .ZIP 라이브러리 추가**에서 `HUSKYLENS_library.zip`을 설치합니다.
2. 네오픽셀 예제는 라이브러리 매니저에서 **Adafruit NeoPixel**도 설치합니다.
3. 실제 보드와 포트를 선택한 뒤 검증·업로드합니다.
4. 시리얼 모니터는 **9600 baud**로 엽니다.

Python 설정 파일을 바꾸면 다음에 Python으로 생성하는 코드에 반영됩니다. 이미 저장된 `.ino`는 자동으로 바뀌지 않습니다.

## 소프트웨어 검사

저장소 루트에서 다음 명령으로 검사합니다.

```powershell
python -B -m unittest discover -s tests -v
```

Python 검사 7개와 호스트 검사 메서드 2개가 있습니다. 호스트 검사는 GCC와 G++가 필요하며, 컴파일러가 없으면 해당 메서드는 건너뜁니다. 두 호스트 메서드는 기본 예제 4개와 색·얼굴 시작/실패/복구 6개, 총 10개 사례를 실행합니다. NeoPixel은 시험용 버퍼로 대체하므로 실제 LED 신호·출력을 검증하지 않습니다.

GitHub에 게시한 뒤에는 `.github/workflows/checks.yml`이 `main` 푸시와 Pull Request에서 같은 검사를 실행합니다. GitHub Actions 실행 결과는 게시 후 확인해야 합니다.

## 검증 범위와 알려진 한계

Python 코드 생성, 호스트 C/C++ 모의 동작, ATmega328P/UNO용 AVR 컴파일 결과는 [VERIFICATION.txt](VERIFICATION.txt)에 기록했습니다. **컴파일·모의 시험 통과는 실제 보드 업로드, 허스키렌즈 화면의 모드 전환, 인식 성능, LED 출력, 전원·배선·주행의 확인을 의미하지 않습니다.**

현재 코드에는 다음 한계가 있습니다.

- 제조사 라이브러리는 결과 배열의 `realloc()` 실패를 검사하지 않습니다. 메모리가 부족한 상황의 정상 복구는 보장되지 않습니다.
- I2C 버스 제한시간 설정은 `WIRE_HAS_TIMEOUT` 매크로에 의존합니다. 코어가 해당 매크로를 제공하지 않으면 설정 코드가 빠질 수 있습니다.
- 센서 요청 내부에서 응답을 기다리는 동안 `stale_ms`를 검사하지 않습니다. `motor()`와 `delay()`의 정지 처리는 요청 전체가 지연되거나 버스가 멈추는 상황에서 정지를 보장하지 않습니다.

첫 주행 시험은 바퀴를 들어 올린 상태에서 진행하고, 연결·인식·모터 방향을 실제 보드에서 확인하세요.

## 라이선스와 출처

이 저장소에서 새로 작성한 확장 모듈·예제·호스트 테스트는 [MIT 라이선스](LICENSE)를 따릅니다. `vendor/HUSKYLENS/`와 `HUSKYLENS_library.zip`의 제조사 소스에는 자체 LGPL 고지가 유지됩니다. 제조사 라이브러리까지 MIT로 변경한 것은 아닙니다. 외부 의존성 `bowcar==1.3.4`는 별도로 설치합니다. 상세 출처와 라이선스는 [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt) 및 [PROVENANCE.json](PROVENANCE.json)을 참고하세요.

## 참고 자료

- [bowcar 1.3.4 — PyPI](https://pypi.org/project/bowcar/1.3.4/)
- [허스키렌즈 색 인식·여러 색 학습](https://wiki.dfrobot.com/sen0305/docs/22645)
- [허스키렌즈 얼굴 인식·학습](https://wiki.dfrobot.com/sen0305/docs/22612)
- [허스키렌즈 I2C 연결](https://wiki.dfrobot.com/sen0305/docs/22766)
- [HUSKYLENS 제조사 Arduino 라이브러리](https://github.com/HuskyLens/HUSKYLENSArduino)
- [Adafruit NeoPixel 라이브러리](https://github.com/adafruit/Adafruit_NeoPixel)
