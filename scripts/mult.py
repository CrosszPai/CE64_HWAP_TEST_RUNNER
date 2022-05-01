
import json
import subprocess
import threading
import pigpio
import time
from schema import Result, Schema


def system_utilization_usage(log_file_name: str = "ps.log") -> subprocess.Popen:
    return subprocess.Popen(
        ["while true; do (echo \" % CPU % MEM ARGS $(date)\" && ps  -e -o pcpu,pmem,args --sort=pcpu | grep 'python3\|pigpiod$' | cut -d\" \" -f1-5 | tail) >> {}; sleep 1; done".format(log_file_name)],
        shell=True,
    )


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


def test(f):
    pi = pigpio.pi()

    script = list[Schema]
    with open("./{}.json".format(f), "r") as readfile:
        script = list[Schema](json.load(readfile))

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
    open("{}_res.json".format(f), "w").close()
    with open("{}_res.json".format(f), "w") as outfile:
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


class sample(threading.Thread):
    def __init__(self, num):
        super(sample, self).__init__()
        self.num = num
        self.start()

    def run(self):
        test(self.num)


rst = pigpio.pi()
error = []
for i in range(1, 8, 1):
    a = system_utilization_usage("ps_{}.log".format(i))
    for j in range(0, 20, 1):
        print("====", "round:", j, ":", i, "====")
        workers = []
        for k in range(i):
            workers.append(sample(i))
        try:
            for w in workers:
                res = w.join()
                if(res == "fail"):
                    error.append({
                        "fail": "fail",
                        "i": i,
                        "j": j,
                        "k": k
                    })
        except:
            print("err", i)
        rst.write(6, 1)
        time.sleep(0.2)
        rst.write(6, 0)
        print("reset")
    a.kill()
    cpus = []
    mems = []
    with open("ps_{}.log".format(i)) as f:
        while f:
            line = f.readline()
            if('pigpiod' in line or 'python' in line):
                target = line.strip().split()
                cpu = float(target[0])
                cpus.append(cpu)
                mem = float(target[1])
                mems.append(mem)
            if(line == ""):
                break
    print(sum(cpus)/len(cpus), sum(mems)/len(mems))
    print("====", i, "====")

with open("./err.json", "w") as errfile:
    errfile.write(json.dumps(error, indent=4))
