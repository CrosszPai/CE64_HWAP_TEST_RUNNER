import json
import pigpio
import time
from testing_schema import Schema,Result

def ftr(a: Result, b: Schema, def_err):
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

    target_input = [event for event in script if event["type"] == "input"]
    target_input = sorted(target_input, key=lambda e: e['at'])
    target_output = [event for event in script if event["type"] == "output"]
    target_output = sorted(target_output, key=lambda e: e['at'])
    target_end = [event for event in script if event["type"] == "end"]

    config = [cfg for cfg in script if cfg["type"] == "accept_error"]
    config = config[0]['value']
    if len(target_end) == 0:
        raise Exception("No end event found")

    target_input_pin = []
    [target_input_pin.append(event["pin"])
     for event in target_input if event["pin"] not in target_input_pin]
    target_output_pin = []
    [target_output_pin.append(event["pin"])
     for event in target_output if event["pin"] not in target_output_pin]

    # setup input
    for pin in target_input_pin:
        pi.set_mode(pin, pigpio.OUTPUT)

    result = []

    # add callback data to result

    first_start = 0

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
        pi.write(target['pin'], 1 if target['capture'] == 'rising' else 0)
        # check if has next target
        if input_pin + 1 < len(target_input):
            next_target = target_input[input_pin + 1]
            # print(next_target['at'] - target['at'], end="\n")
            time.sleep(next_target['at'] - target['at'])

    sorted_at = sorted(script, key=lambda x: x['at'])

    # wait for end
    time.sleep(target_end[0]["at"] - sorted_at[-2]['at'])
    for cb in cbs:
        cb.cancel()
    pi.stop()
    # print("end", target_end[0]["at"] - sorted_at[-2]['at'])
    open('result.json', "w").close()
    with open('result.json', "w") as outfile:
        outfile.write(json.dumps(result, indent=4))

    event_test = target_input+target_output
    if(len(result) != len(event_test)):
        # print("fail")
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
        # print("fail")
        return "fail"
    else:
        # print("pass")
        return "pass"