바우카 + 허스키렌즈 1 / v0.1 업로드 테스트 2개
작성일: 2026-10-12

두 파일 모두 UploadBowCar를 상속한 HuskyLensBowCar를 사용합니다.
파이썬 파일을 실행하면 Arduino CLI로 컴파일·업로드합니다.
업로드 후에는 MCU의 loop()에서 독립적으로 동작합니다.
색 인식과 얼굴 인식은 서로 다른 알고리즘을 사용하는 별도 프로그램입니다.
둘 중 원하는 프로그램 하나를 업로드해서 시험하세요.
전원이 켜지면 setup()에서 허스키렌즈에 연결하고, 색 프로그램은 Color Recognition,
얼굴 프로그램은 Face Recognition으로 먼저 전환합니다. 연결 또는 모드 전환
응답에 실패하면 모터를 정지한 상태로 반복 실행 중 다시 시도합니다.

파일
  upload_settings.py       USB 포트·보드·모터 극성 설정
  upload_color_neopixel.py 색 ID별 네오픽셀 색 변경, 모터는 항상 정지
  upload_face_follow.py    학습한 얼굴의 x 좌표에 따른 조향/전진
  bowcar_huskylens.py      허스키렌즈 연결·시작 모드 전환 확장 모듈
  generated/color_neopixel/color_neopixel.ino   색 인식 업로드 스케치
  generated/face_follow/face_follow.ino         얼굴 추종 업로드 스케치
  HUSKYLENS_library.zip    Arduino IDE용 제조사 라이브러리
  vendor/HUSKYLENS/        Arduino CLI에 전달할 제조사 소스
  VERIFICATION.txt        검증 범위와 결과

공통 준비

1. 이 묶음의 폴더에서 다음 명령으로 bowcar 1.3.4를 설치합니다.
     python -m pip install -r requirements.txt
2. Arduino CLI를 설치하고 PATH에 등록하고, 실제 보드의 코어를 설치합니다.
3. upload_settings.py의 기본 PORT=None은 Arduino/CH340 USB 포트를 자동 탐색합니다.
   대상 포트가 하나면 자동 선택합니다. 없거나 여러 개면 포트를 직접 지정합니다.
   현재 연결 포트를 직접 지정하려면 PORT="COM11"처럼 설정합니다.
   macOS/Linux에서는 실제 /dev/... 포트를 입력합니다.
4. 기본 FQBN은 arduino:avr:uno입니다.
   ATmega328P / Arduino UNO 호환 보드·부트로더 기준이며 MiniCore는 필요하지 않습니다.
   Arduino AVR Boards 코어를 사용합니다. 기존에 업로드가 성공했던 설정이
   있다면 그 설정을 사용하세요.
5. 허스키렌즈의 General Settings → Protocol Type → I2C를 선택합니다.

배선은 SDA=A4/PC4, SCL=A5/PC5입니다. 제공된 J5 회로도의 빨간 수정이
반영된 보드라면 SDA=J5 8번, SCL=J5 6번입니다. 수정 전 도면은 반대이므로
실물 연결을 확인해야 합니다. GND는 공통으로 연결하고 카메라 전원은
3.3~5.0V 사양 범위인지 확인합니다.

색 인식 → 네오픽셀

처음 학습할 때 허스키렌즈에서 Color Recognition 모드를 선택하고 Learn Multiple을 켭니다.
빨강, 초록, 파랑을 순서대로 학습시켜 화면 표시가 다음과 같도록 준비합니다.
  빨강: Color ID1 / 초록: Color ID2 / 파랑: Color ID3
학습 ID는 색 자체에 고정된 번호가 아니라 학습한 순서의 번호입니다.
프로그램 시작 시에는 Color Recognition 모드로 자동 전환합니다.

업로드:
  python upload_color_neopixel.py

이 파일은 업로드 전에 Arduino CLI로 Adafruit NeoPixel 라이브러리를
확인/설치합니다. 첫 설치에는 인터넷 연결이 필요할 수 있습니다.
바우카 기본 네오픽셀 데이터 핀 D9, LED 4개, GRB 형식을 사용합니다.
ID1이면 4개 모두 빨강, ID2이면 초록, ID3이면 파랑으로 바뀝니다.
대상 없음, 다른 ID, 통신 실패에서는 꺼집니다. 모터는 항상 정지합니다.
여러 색이 함께 인식되면 사각형 면적이 가장 큰 학습 대상의 ID를 사용합니다.
밝기는 upload_color_neopixel.py의 BRIGHTNESS(기본 50, 0~255)로 조절합니다.

얼굴 x 좌표 → 바우카 추종

Face Recognition 모드에서 따라갈 얼굴을 먼저 학습하고 Face ID1이
표시되는지 확인합니다. 처음에는 바퀴를 바닥에서 띄우고 방향을 확인하세요.
프로그램 시작 시에는 Face Recognition 모드로 자동 전환합니다.

업로드:
  python upload_face_follow.py

기본값 TARGET_FACE_ID=1이므로 학습한 얼굴 ID1만 따라갑니다.
TARGET_FACE_ID=None으로 바꾸면 학습된 얼굴 중 사각형 면적이 가장 큰
얼굴을 선택합니다. 학습하지 않은 얼굴(ID0)은 따라가지 않습니다.

기본 조향:
  x < 135          왼쪽 모터 50, 오른쪽 모터 130 → 왼쪽 조향
  135 ≤ x ≤ 185    양쪽 모터 90 → 전진
  x > 185          왼쪽 모터 130, 오른쪽 모터 50 → 오른쪽 조향

얼굴이 사라지거나 통신이 실패하면 정지합니다.
얼굴 사각형 너비가 STOP_FACE_WIDTH(기본 120픽셀) 이상이어도 정지합니다.
이 기준은 거리(cm)가 아니므로 실제 촬영 조건에 맞게 조정해야 합니다.
CENTER_X, DEADBAND, BASE_SPEED, TURN_SPEED, STOP_FACE_WIDTH를 파일
위쪽에서 바꿀 수 있습니다. 기본값은 화면 중앙 x=160, 중심 허용 범위 ±25,
기본 속도 90, 조향 속도 차이 40입니다. 속도는 PWM 값입니다.
바퀴가 반대로 돌면 upload_settings.py에서 해당 POLARITY를 -1로 바꿉니다.
인식 상태는 바우카의 빨강/파랑 LED와 시리얼 로그로 표시합니다.

Arduino IDE에서 바로 업로드하려면

파이썬 실행 없이 generated 폴더의 .ino를 직접 열어 업로드할 수도 있습니다.
HUSKYLENS_library.zip을 IDE의 “.ZIP 라이브러리 추가”로 설치하세요.
색 인식 예제에는 라이브러리 매니저의 Adafruit NeoPixel도 필요합니다.
실제 보드/포트를 선택한 뒤 검증과 업로드를 실행합니다.
Python의 설정 파일을 바꾸면 해당 Python 프로그램에서 생성하는 코드에
반영됩니다. 이미 들어 있는 .ino는 위 기본값으로 생성된 파일입니다.
시리얼 모니터 속도는 두 프로그램 모두 9600 baud입니다.

허스키렌즈 함수 목록

아래 목록은 이 폴더의 bowcar_huskylens.py에 있는 Python 함수 기준입니다.
Python은 PC에서 Arduino 프로그램을 생성합니다. 카메라 연결, 모드 전환,
인식 결과 읽기와 모터 제어는 업로드 후 바우카 MCU에서 실행됩니다.

시작과 결과 갱신:
  begin_huskylens()
    setup()에서 카메라에 연결하고 생성자에 지정한 인식 모드로 전환합니다.
    프로그램을 만들 때 생성자 다음에 한 번 호출합니다.
    연결이나 모드 설정에 실패하면 loop()에서 다시 시도합니다.
  read_huskylens()
    loop()에 인식 결과를 읽는 코드를 추가합니다.
    대상 상태나 좌표를 사용하는 코드보다 앞에 두세요.
    대상이 없거나 요청에 실패하면 ID와 좌표·크기는 0으로 초기화됩니다.

연결과 대상 확인:
  is_camera_connected()
    카메라 연결·모드 설정 및 최근 통신 상태를 나타내는 표현식입니다.
    이 함수만 호출해서 새 통신 요청을 보내는 것은 아닙니다.
  has_target()
    지정한 학습 ID와 좌표 조건에 맞는 대상이 검출됐는지 확인합니다.
  get_target_id()
    선택한 대상의 학습 ID입니다. 색 인식에서도 RGB 값이 아닌 학습 ID입니다.

사각형과 선 좌표:
  get_target_x(), get_target_y()
    사각형 중심의 x/y 좌표입니다. 선 추적에서는 화살표 끝점 좌표입니다.
  get_target_width(), get_target_height()
    사각형의 너비/높이입니다. 단위는 픽셀이며 거리(cm)가 아닙니다.
    선 추적에서는 사각형 크기를 사용하지 않습니다.
  get_arrow_x_origin(), get_arrow_y_origin()
    Line Tracking 화살표 시작점의 x/y 좌표입니다.
  get_arrow_x_target(), get_arrow_y_target()
    Line Tracking 화살표 끝점의 x/y 좌표입니다.

반복 실행과 진단:
  debug_huskylens(interval_ms=250)
    지정 주기로 camera/target/id/x/y/w/h를 시리얼 모니터에 출력합니다.
    기본 주기는 250ms, 시리얼 모니터 속도는 9600 baud입니다.
  motor(left, right)
    대상 유효성을 검사하면서 모터를 제어합니다.
    속도는 -255~255이며 정수 또는 하나의 C++ 속도 표현식을 입력합니다.
    대상이 없거나 결과가 오래되었으면 이 함수에서 모터를 정지합니다.
  delay(ms)
    지연 코드를 추가합니다. 지연 중 결과가 오래되면 모터를 정지합니다.
    MCU가 다른 함수에서 멈춘 상황까지 감시하는 하드웨어 워치독은 아닙니다.

파일 생성과 컴파일·업로드:
  export_sketch(directory)
    지정한 폴더에 같은 이름의 .ino를 생성하고 파일 경로를 반환합니다.
    예: generated/color_id_example/color_id_example.ino
    마지막 폴더 이름은 color_id_example처럼 영문·숫자·밑줄을 사용하며,
    첫 글자는 영문 또는 밑줄이어야 합니다.
  compile_code(directory=..., fqbn=...)
    Arduino CLI로 컴파일만 수행하고 .ino 경로를 반환합니다.
    fqbn은 생성자에서 지정한 값을 사용하거나 이 호출에서 지정합니다.
  upload_code(port=None, directory=..., fqbn=...)
    Arduino CLI로 컴파일한 뒤 업로드하고 .ino 경로를 반환합니다.
    port=None이면 Arduino/CH340 포트를 자동 탐색합니다.
    대상 포트가 없거나 여러 개이면 COM11처럼 포트를 직접 지정합니다.

인식 모드와 대상 설정

HuskyLensBowCar(...)를 만들 때 algorithm과 target_id를 지정합니다.
실행 중 모드를 바꾸는 별도의 Python 함수는 현재 제공하지 않습니다.
begin_huskylens()는 생성자에서 정한 모드를 시작 시 적용합니다.

algorithm 값:
  color_recognition       Color Recognition / 색 인식
  face_recognition        Face Recognition / 얼굴 인식
  object_tracking         Object Tracking / 물체 추적
  object_recognition      Object Recognition / 물체 인식
  line_tracking           Line Tracking / 선 추적
  tag_recognition         Tag Recognition / 태그 인식
  object_classification   Object Classification / 물체 분류

주요 생성자 설정:
  target_id=1       학습 ID 1만 선택합니다. 다른 학습 ID를 지정할 수도 있습니다.
  target_id=None    학습된 ID 전체를 대상으로 하며 미학습 ID 0은 제외합니다.
  selection="largest"    가장 큰 사각형을 선택합니다. 기본값입니다.
  selection="lowest_id"  작은 학습 ID를 우선 선택합니다.
  timeout_ms=100    제조사 라이브러리의 응답 대기 시간입니다.
                   전체 인식 요청 시간이 항상 100ms 이내라는 뜻은 아닙니다.
  retry_ms=1000     연결·모드 설정 실패 후 재시도 간격입니다.
  stale_ms=300      motor()/delay()에서 오래된 결과를 판정하는 기준입니다.
                   timeout_ms보다 커야 합니다.
  left_polarity/right_polarity    각 모터 방향입니다. 1 또는 -1을 사용합니다.
  fqbn             실제 보드 설정입니다. 이 묶음은 arduino:avr:uno를 사용합니다.

결과 함수는 Python의 숫자나 bool 대신 MCU에서 평가할 C++ 표현식 문자열을
반환합니다. 따라서 일반 Python if 대신 with car.bif(...), car.belif(...),
car.belse()를 사용하세요. Python의 print(car.get_target_x())는 실제 센서
좌표를 읽는 방법이 아닙니다. 인식 결과 출력에는 debug_huskylens()를 사용합니다.

간단한 사용 예제

이 폴더에 아래 이름의 Python 파일을 만들어 실행하세요. 두 예제는 .ino
파일 생성만 수행합니다. 생성한 프로그램에서는 모터를 항상 정지합니다.
색·얼굴 학습과 I2C 설정은 위의 공통 준비 및 각 프로그램 설명을 따릅니다.

예제 1: 색 ID1이면 네오픽셀을 빨강으로 켜기 — color_id_example.py

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

실행:
  python color_id_example.py

생성 파일: generated/color_id_example/color_id_example.ino
시작 시 Color Recognition으로 전환합니다. 학습된 색 중 가장 큰 대상이
ID1일 때 빨강으로 켜지고, 그 밖의 ID·미검출·통신 실패에서는 꺼집니다.
neopixel_brightness()/neopixel_all()/neopixel_clear()는 기존 bowcar의
네오픽셀 함수입니다. 컴파일에는 Adafruit NeoPixel 라이브러리가 필요합니다.
이 예제를 직접 업로드할 경우 먼저 다음 명령으로 설치하세요.
  arduino-cli lib install "Adafruit NeoPixel"

예제 2: 학습한 얼굴 ID1을 감지하면 파랑 LED 켜기 — face_detect_example.py

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

실행:
  python face_detect_example.py

생성 파일: generated/face_detect_example/face_detect_example.ino
시작 시 Face Recognition으로 전환합니다. 얼굴 ID1이 검출되면 파랑 LED,
미검출·통신 실패에서는 빨강 LED가 켜집니다. blue()/red()는 기존 bowcar의
LED 함수입니다. 실제 얼굴 좌표와 크기는 시리얼 모니터 로그에서 확인합니다.
얼굴을 따라 주행하는 예제는 기존 upload_face_follow.py를 사용하세요.

예제를 컴파일하거나 업로드하려면

예제의 ino = car.export_sketch(output_dir) 한 줄을 다음 중 하나로 바꿉니다.
컴파일만 수행:
  ino = car.compile_code(directory=output_dir)
컴파일·업로드:
  from upload_settings import PORT
  ino = car.upload_code(port=PORT, directory=output_dir)

PORT=None이면 현재 연결된 Arduino/CH340 포트를 자동 선택합니다.
포트를 직접 지정하려면 upload_settings.py에서 PORT="COM11"로 설정합니다.

검증

이 문서의 간단한 사용 예제 2개는 Python 3.8 문법 검사, 코드 생성,
ATmega328P / arduino:avr:uno 컴파일을 통과했습니다.
생성 코드의 호스트 C/C++ 컴파일 및 I2C 모의 동작을 확인했습니다.
추가로 ATmega328P / arduino:avr:uno 설정에서 두 프로그램의 AVR 컴파일과
정적 메모리 사용량을 확인했습니다. 실제 USB 업로드, 네오픽셀 출력과
주행은 아직 실물에서 확인하지 않았습니다. 자세한 범위는 VERIFICATION.txt에 있습니다.

공식 참고
  색 인식/여러 색 학습: https://wiki.dfrobot.com/sen0305/docs/22645
  얼굴 인식/학습: https://wiki.dfrobot.com/sen0305/docs/22612
  I2C 설정: https://wiki.dfrobot.com/sen0305/docs/22766
  NeoPixel 라이브러리: https://github.com/adafruit/Adafruit_NeoPixel
