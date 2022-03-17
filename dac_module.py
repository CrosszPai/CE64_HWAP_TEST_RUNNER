import board
import busio

import adafruit_mcp4725

class DAC:
    def __init__(self) -> None:
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.dac = adafruit_mcp4725.MCP4725(self.i2c, address=0x60)

    def set_voltage(self, voltage: float) -> None:
        """
        Set the voltage of the DAC.
        """
        assert voltage >= 0.0
        assert voltage <= 3.3
        self.dac.raw_value = int(voltage * 4095 / 3.3)
    def set_voltage_raw(self, value: int) -> None:
        """
        Set the voltage of the DAC.
        """
        assert value >= 0
        assert value <= 4095
        self.dac.raw_value = value
