import numpy as np
import matplotlib.pyplot as plt
from encodings import utf_8
import json
from time import sleep
import pigpio

from pwm_reader import PWMreader
import serial


def collect_data():
    pi = pigpio.pi()
    a = PWMreader(pi, 20, 0.1, False)

    ser = serial.Serial('/dev/serial0', 115200)
    print("open serial port")
    print(ser.is_open)
    ser.flush()
    start = 1
    end = 101
    data = []
    while True:
        received_data = ser.readline()  # read serial port
        dat = received_data.strip().decode('utf-8')
        if dat == "start":
            sleep(0.5)
            data.append(a.evaluate_pwm(1, 0.2))
            start += 1
            print("next ", start)
        if(start == end):
            break

    json.dump(data, open("data_pwm.json", "w"), indent=4)


# plot graph from data_pwm.json

datas = json.load(open("data_pwm.json"))

x = np.linspace(1, 101, 100)
y = []

expected_y = np.array([i for i in range(1, 101, 1)])

for i in range(len(datas)):
    y.append(datas[i]['duty_cycle'])

y = np.array(y)

plt.xlabel('simulation duty cycle')
plt.ylabel('real duty cycle')

plt.plot(x, y, 'r-')
plt.plot(x, expected_y, 'b-')

plt.show()
plt.savefig('plot_pwm.png')
