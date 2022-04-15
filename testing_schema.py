from typing_extensions import TypedDict


class Schema(TypedDict):
    label: str # Label of the measurement <optional>
    pin: int # target pin <required>
    type: str # input or output
    signal: str # digtal(default) analog pwm
    at: int # time
    unit: str # time unit default: microseconds
    capture: str # falling or rising ignore if input analog signal
    value: int # assigned or expected value
    accept_error: str # error threshold ignore if is input type
    relative_to: str # force to be relative to another measurement <optional>
    
    # special fields for pwm
    measure_time: int # measure time of pwm
    duty_cycle: int # duty cycle of pwm
    frequency: int # frequency of pwm

    

