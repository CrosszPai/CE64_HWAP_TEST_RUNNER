import math
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
import json

from sklearn.metrics import mean_squared_error

x = np.linspace(0, 4095, 4096)
file = open('data_adc.txt', 'r')

dat = file.readlines()
real = []
for line in dat:
    l = json.loads(line)
    avg = sum(l)/len(l)
    real.append(avg)


y = np.array(real)


def func_simple(x, a, b):
    return a * x + b


popt, pcov = curve_fit(func_simple, x, y, bounds=(0, np.inf))
plt.plot(x, func_simple(x, *popt), 'r-',
         label='fit: a=%5.3f, b=%5.3f' % tuple(popt))
plt.plot(x, y, 'b-', label='data')
plt.xlabel('x')
plt.ylabel('y')
plt.legend()
plt.show()
plt.savefig('plot.png')

print(math.sqrt(mean_squared_error(x, func_simple(x, *popt))),
      mean_squared_error(x, func_simple(x, *popt)))

# for i in range(100):
# print(i,":",func_simple(i, *popt))
# [9.91291133e-01 8.55857284e-25]
print(popt)
