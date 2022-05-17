from enum import auto
import json
import time
from typing import TypedDict
import pigpio  # http://abyz.co.uk/rpi/pigpio/python.html


class PWMdata(TypedDict):
    frequency: float
    pulse_width: float
    duty_cycle: float


class PWMreader:
    """
    A class to read PWM pulses and calculate their frequency
    and duty cycle.  The frequency is how often the pulse
    happens per second.  The duty cycle is the percentage of
    pulse high time per cycle.
    """

    def __init__(self, pi, gpio, weighting=0.0, auto_cancel=True):
        """
        Instantiate with the Pi and gpio of the PWM signal
        to monitor.

        Optionally a weighting may be specified.  This is a number
        between 0 and 1 and indicates how much the old reading
        affects the new reading.  It defaults to 0 which means
        the old reading has no effect.  This may be used to
        smooth the data.
        auto_cancel: if True, cancel the reader after evaluating
        """
        self.pi = pi
        self.gpio = gpio
        self.auto_cancel = auto_cancel

        if weighting < 0.0:
            weighting = 0.0
        elif weighting > 0.99:
            weighting = 0.99

        self._new = 1.0 - weighting  # Weighting for new reading.
        self._old = weighting       # Weighting for old reading.

        self._high_tick = None
        self._period = None
        self._high = None

        pi.set_mode(gpio, pigpio.INPUT)

        self._cb = pi.callback(gpio, pigpio.EITHER_EDGE, self._cbf)

    def _cbf(self, gpio, level, tick):

        if level == 1:

            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if self._period is not None:
                    self._period = (self._old * self._period) + (self._new * t)
                else:
                    self._period = t

            self._high_tick = tick

        elif level == 0:

            if self._high_tick is not None:
                t = pigpio.tickDiff(self._high_tick, tick)

                if self._high is not None:
                    self._high = (self._old * self._high) + (self._new * t)
                else:
                    self._high = t

    def frequency(self):
        """
        Returns the PWM frequency.
        """
        if self._period is not None:
            return 1000000.0 / self._period
        else:
            return 0.0

    def pulse_width(self):
        """
        Returns the PWM pulse width in microseconds.
        """
        if self._high is not None:
            return self._high
        else:
            return 0.0

    def duty_cycle(self):
        """
        Returns the PWM duty cycle percentage.
        """
        if self._high is not None:
            return 100.0 * self._high / self._period
        else:
            return 0.0

    def cancel(self):
        """
        Cancels the reader and releases resources.
        """
        self._cb.cancel()

    def evaluate_pwm(self, run_time, sample_time):
        start_time = time.time()
        data = []
        while (time.time() - start_time) < run_time:
            time.sleep(sample_time)
            f = self.frequency()
            pw = self.pulse_width()
            dc = self.duty_cycle()
            data.append([f, pw, dc])
        # find avaerage of data
        sum_f = 0
        sum_pw = 0
        sum_dc = 0
        for i in range(len(data)):
            sum_f += data[i][0]
            sum_pw += data[i][1]
            sum_dc += data[i][2]
        avg_f = sum_f / len(data)
        avg_pw = sum_pw / len(data)
        avg_dc = sum_dc / len(data)
        if self.auto_cancel:
            self.cancel()

        return PWMdata(frequency=avg_f, pulse_width=avg_pw, duty_cycle=avg_dc)


# pi = pigpio.pi()
# a = PWMreader(pi, 20)
# print(json.dumps(a.evaluate_pwm(5, 2), indent=4))
# a.cancel()
