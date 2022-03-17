from typing_extensions import TypedDict


class Schema(TypedDict):
    label: str # Label of the measurement
    pin: int # target pin
    event: str # falling or rising
    at: int # time
    unit: str # time unit
    type: str # input or output
    value: str # assigned or expected value
    signal: str # digtal(default) analog pwm
    accept_error: str # error threshold
    relative_to: str # force to be relative to another measurement
    
    # special fields for pwm
    measure_time: int # measure time of pwm

    

