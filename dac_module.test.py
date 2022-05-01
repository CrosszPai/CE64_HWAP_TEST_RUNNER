from time import sleep, time
from dac_module import DAC
import serial


s = DAC()
s.set_voltage_raw(0)
sleep(10)
start = 1
count = 0
max_val = 4096
max_count = 1000

# ser = serial.Serial('/dev/serial0', 115200)
# print("open serial port")
# print(ser.is_open)
# ser.flush()

# while True:
#     received_data = ser.readline()  # read serial port
#     print(int(received_data.decode('utf-8')))  # print received data

datas = []
for i in range(max_val):
    count = 0
    dat = []
    s.set_voltage_raw(i)
    while True:
        if count == max_count:
            break
        received_data = ser.readline()  # read serial port
        data = int(received_data.decode('utf-8'))
        dat.append(data)
        count += 1
    datas.append(dat)
    print('got',i)
file = open("data_adc.txt", "w")
# write datas to file
for i in range(max_val):
    file.write(str(datas[i]))
    file.write("\n")
file.close()
