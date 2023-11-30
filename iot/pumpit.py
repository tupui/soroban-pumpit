import time
import threading

import numpy as np
import pandas as pd
from gpiozero import Button, LED, RGBLED


# hardware setup
clear_pump = Button(2)
flow_meter = Button(3)

rgb_led = RGBLED(red=9, green=10, blue=11)  # rgb_led.color = (0, 1, 0)
red_led = LED(17)  # red_led.on()
green_led = LED(27)


class Pump:
    def __init__(self) -> None:
        self.ticks = []
        self.flow_history = []

        self._lock = threading.Lock()

    def clear(self) -> None:
        with self._lock:
            self.ticks = []
            self.flow_history = []

    def tick(self) -> None:
        self.ticks.append(pd.Timestamp(time.perf_counter_ns()))

    def volume(self) -> float:
        """Total volume seen by the pump in L."""
        return len(self.flow_history) / 480.

    def flow_rate(self, window: str = "3s") -> float:
        """Flow rate.

        Count the ticks per seconds and convert to a flow rate in L/MIN.
        Then return the last rolling mean.
        """
        # acquire lock to not add new ticks while reading the list. Could lose some ticks
        with self._lock:
            data = pd.DataFrame(np.arange(len(self.ticks)), index=self.ticks)
            self.flow_history.append(*self.ticks)
            self.ticks = []

        # ticks at 16Hz = 120 L/H
        q = data.rolling("1s").sum() / 8.  # 480 for L/H
        return q.rolling(window).mean().iloc[0, -1]


pump = Pump()
flow_meter.when_pressed = pump.tick
clear_pump.when_activated = pump.clear

# logic starts here
max_pumping_volume = 3.

# green LED says we are ready for business and can start pumping
green_led.on()
# RGB LED is more and more green as we pump
rgb_led.on()

while "Pumping":
    time.sleep(7)
    curr_volume = pump.volume()
    print(f"Flow rate: {pump.flow_rate()} L/M and we pumped {curr_volume} L")

    if curr_volume > max_pumping_volume:
        green_led.off()
        red_led.blink(on_time=0.25, off_time=0.25, n=4*5)
        pump.clear()
        rgb_led.off()
        print("Calling Soroban smart contract")
        # call Soroban contract
    else:
        rgb_led.color = (0, curr_volume / max_pumping_volume, 0)
