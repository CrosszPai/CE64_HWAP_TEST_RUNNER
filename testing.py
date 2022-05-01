import json
import pigpio
import time
from dac_module import DAC
from testing_schema import Schema, Result


def ftr(a: Result, b: Schema, def_err):
    if(a.get('signal') == 'analog' and b.get('value') == a.get('value')):
        if(b.get('accept_error') is not None):
            diff = abs(a['relative_timestamp'] - b['at'])
            if(diff > b["accept_error"]):
                return False
            return True
        diff = abs(a['relative_timestamp'] - b['at'])
        return diff <= def_err
    diff = abs(a['relative_timestamp'] - b['at'])
    if(a.get('pin') != b.get('pin')):
        return False
    if(a.get('capture') != b.get('capture')):
        return False
    if(b.get('accept_error') is not None):
        diff = abs(a['relative_timestamp'] - b['at'])
        if(diff > b["accept_error"]):
            return False
        return True
    diff = abs(a['relative_timestamp'] - b['at'])
    return diff <= def_err


def test(imported_script):
    pi = pigpio.pi()

    script = imported_script

    # print(script)
    # parsing any input
    target_input: list[Schema] = [
        event for event in script if event["type"] == "input"]
    target_input = sorted(target_input, key=lambda e: e['at'])
    target_output: list[Schema] = [
        event for event in script if event["type"] == "output"]
    target_output = sorted(target_output, key=lambda e: e['at'])
    target_end: list[Schema] = [
        event for event in script if event["type"] == "end"]

    config = [cfg for cfg in script if cfg["type"] == "accept_error"]
    config = config[0]['value']
    if len(target_end) == 0:
        raise Exception("No end event found")

    target_input_pin = []
    [target_input_pin.append(event["pin"])
     for event in target_input if event["pin"] not in target_input_pin and event["signal"] != "analog"]
    target_output_pin = []
    [target_output_pin.append(event["pin"])
     for event in target_output if event["pin"] not in target_output_pin]

    # setup input
    for pin in target_input_pin:
        pi.set_mode(pin, pigpio.OUTPUT)

    result = []

    # add callback data to result

    first_start = 0
    dac = DAC()
    dac.set_voltage_raw(0)
    # keep any program cold
    time.sleep(2)

    def callback(gpio, level, tick):
        nonlocal first_start, result
        if first_start == 0:
            first_start = tick
        result.append(
            {
                "pin": gpio,
                "capture": "falling" if level == 0 else "rising",
                "timestamp": tick,
                "relative_timestamp": (tick - first_start)/1000000
            }
        )

    # set all callback
    cbs = []
    for input_pin in target_input_pin:
        w = pi.callback(input_pin, pigpio.EITHER_EDGE, callback)
        cbs.append(w)

    for output_pin in target_output_pin:
        w = pi.callback(output_pin, pigpio.EITHER_EDGE, callback)
        cbs.append(w)

    # start

    for input_pin in range(len(target_input)):
        target = target_input[input_pin]
        # print(target, end="\n")
        if target['signal'] == "analog":
            dac.set_voltage_raw(target['value'])
            result.append({
                "pin": "analog_pin",
                "signal": "analog",
                "relative_timestamp": target['at'],
                "value": target['value']
            })
        else:
            pi.write(target['pin'], 1 if target['capture'] == 'rising' else 0)
        # check if has next target
        if input_pin + 1 < len(target_input):
            next_target = target_input[input_pin + 1]
            # print(next_target['at'] - target['at'], end="\n")
            time.sleep(next_target['at'] - target['at'])

    sorted_at = sorted(script, key=lambda x: x['at'])

    # wait for end
    time.sleep(target_end[0]["at"] - sorted_at[-2]['at'])

    # release callback
    for cb in cbs:
        cb.cancel()
    pi.stop()
    dac.set_voltage_raw(0)
    print(json.dumps(result, indent=4))
    open('result.json', "w").close()
    with open('result.json', "w") as outfile:
        # clone last result
        dumb = result.copy()
        last_dumb = {
            "pin": dumb[-1].get('pin', None),
            "capture": dumb[-1].get('capture', None),
            "relative_timestamp": target_end[0]["at"],
            "value": dumb[-1].get('value', None)
        }
        dumb.append(last_dumb)
        outfile.write(json.dumps(dumb, indent=4))

    event_test = target_input+target_output
    if(len(result) != len(event_test)):
        print("fail", "len")
        return "fail"

    count = 0
    # print(len(result))
    for sc in range(len(event_test)):
        f = list(filter(lambda r: ftr(r, event_test[sc], config), result))
        if len(f) == 1:
            count = count + 1
            # print("pass", json.dumps(
            #     event_test[sc], indent=4), json.dumps(f[0], indent=4))
            continue
        # print("fail", json.dumps(
        #     event_test[sc], indent=4))
        return "fail"

    if count != len(event_test):
        return "fail"
    else:
        # print("pass")
        return "pass"
