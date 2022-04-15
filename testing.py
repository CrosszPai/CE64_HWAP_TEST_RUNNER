import json
import threading
import pigpio
import time

from utils import system_utilization_usage

a = system_utilization_usage()

pi = pigpio.pi()

register_pins = dict({
    1:{
        "label": "lab_1",
        "pins":[]
    },
    2:{
        "label": "lab_2",
        "pins":[]
    },
    3:{
        "label": "lab_3",
        "pins":[]
    },
    4:{
        "label": "lab_1",
        "pins":[]
    },
})

script = []
with open("./lab_1.json", "r") as readfile:
    script = json.load(readfile)

# print(script)

target_input = [event for event in script if event["type"] == "input"]
target_output = [event for event in script if event["type"] == "output"]
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
    global first_start, result
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

for input_pin in target_input_pin:
    pi.callback(input_pin, pigpio.EITHER_EDGE, callback)

for output_pin in target_output_pin:
    pi.callback(output_pin, pigpio.EITHER_EDGE, callback)

# start

for input_pin in range(len(target_input)):
    target = target_input[input_pin]
    print(target,end="\n")
    pi.write(target['pin'], 1 if target['capture'] == 'rising' else 0)
    # check if has next target
    if input_pin + 1 < len(target_input):
        next_target = target_input[input_pin + 1]
        print(next_target['at'] - target['at'], end="\n")
        time.sleep(next_target['at'] - target['at'])

with open("sample.json", "w") as outfile:
    outfile.write(json.dumps(result, indent=4))

a.kill()