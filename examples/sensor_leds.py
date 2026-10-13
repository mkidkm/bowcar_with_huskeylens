"""Read button/light/sound/line values; motors always remain stopped."""
from _teaching import prepare, finish

LIGHT_THRESHOLD = 500
SOUND_THRESHOLD = 500
LINE_THRESHOLD = 500


def build(car, sensor="button"):
    if sensor not in ("button", "light", "sound", "line"):
        raise ValueError("Choose button, light, sound, or line")
    car.begin_diagnostics()
    car.motor(0, 0)
    fields = [("u", car.get_button("u")), ("d", car.get_button("d")),
              ("l", car.get_button("l")), ("r", car.get_button("r")),
              ("light", car.get_light()), ("sound", car.get_sound()),
              ("line_l", car.get_line("l")), ("line_r", car.get_line("r"))]
    for label, expression in fields:
        car.set_value("int", "tc_" + label, expression)
    if sensor == "button":
        red_condition, blue_condition = "tc_d", "tc_u"
    elif sensor == "light":
        red_condition = "tc_light < {}".format(LIGHT_THRESHOLD)
        blue_condition = "tc_light >= {}".format(LIGHT_THRESHOLD)
    elif sensor == "sound":
        red_condition = "tc_sound <= {}".format(SOUND_THRESHOLD)
        blue_condition = "tc_sound > {}".format(SOUND_THRESHOLD)
    else:
        red_condition = "tc_line_l < {}".format(LINE_THRESHOLD)
        blue_condition = "tc_line_r < {}".format(LINE_THRESHOLD)
    with car.bif(red_condition):
        car.red("on")
    with car.belse():
        car.red("off")
    with car.bif(blue_condition):
        car.blue("on")
    with car.belse():
        car.blue("off")
    car.debug_values([(label, "tc_" + label) for label, _ in fields], 250)
    car.delay(50)


def options(parser):
    parser.add_argument("--sensor", choices=("button", "light", "sound", "line"), default="button")


if __name__ == "__main__":
    car, args = prepare("sensor_leds", "센서값 시리얼 출력과 LED 조건 제어; 모터 정지", options)
    build(car, args.sensor)
    finish(car, args)
