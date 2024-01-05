import os
from signal import pause
import time
import threading

import numpy as np
import pandas as pd
from gpiozero import Button, LED, RGBLED

from soroban import soroban_claim

CONTRACT_HASH_PUMPIT = os.getenv("CONTRACT_HASH_PUMPIT")
CLAIMANT_ADDR_SECRET_PUMPIT = os.getenv("CLAIMANT_ADDR_SECRET_PUMPIT")

if CONTRACT_HASH_PUMPIT is None or CLAIMANT_ADDR_SECRET_PUMPIT is None:
    raise ValueError(
        "Missing environment variables CONTRACT_HASH_PUMPIT and CLAIMANT_ADDR_SECRET_PUMPIT"
    )

# hardware setup
clear_pump = Button(2)
flow_meter = Button(26)

rgb_led = RGBLED(red=9, green=10, blue=11)
red_led = LED(5)
green_led = LED(6)


class Pump:
    def __init__(self) -> None:
        self.ticks = []
        self.flow_history = []

        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self.ticks = []
            self.flow_history = []

    def tick(self) -> None:
        with self._lock:
            self.ticks.append(pd.Timestamp(time.perf_counter_ns()))

    def volume(self) -> float:
        """Total volume seen by the pump in L."""
        with self._lock:
            return len(self.flow_history) / 480.

    def flow_rate(self, window: str = "1s") -> float:
        """Flow rate.

        Count the ticks per seconds and convert to a flow rate in L/MIN.
        Then return the last rolling mean.
        """
        # acquire lock to not add new ticks while reading the list. Could lose some ticks
        with self._lock:
            n_ticks = len(self.ticks)
            if n_ticks == 0:
                return 0.
            data = pd.DataFrame(np.ones(n_ticks), index=self.ticks)
            self.flow_history += self.ticks

        if n_ticks > 1_000_000:  # avoid memory issues
            self.clear()

        # ticks at 16Hz = 120 L/H
        q = data.rolling("1s").sum() / 8.  # 480 for L/H
        return q.rolling(window).mean().iloc[-1, 0]


pump = Pump()
flow_meter.when_pressed = pump.tick
clear_pump.when_activated = pump.clear

# logic starts here
max_pumping_volume = 10.

# green LED says we are ready for business and can start pumping
green_led.on()
# RGB LED is more and more green as we pump
rgb_led.on()

rgb_led.color = (0, 0, 0)

while "Pumping":
    time.sleep(1)
    curr_volume = pump.volume()
    print(f"Flow rate: {pump.flow_rate()} L/M and we pumped {curr_volume} L")

    if curr_volume > max_pumping_volume:
        green_led.off()
        red_led.blink(on_time=0.25, off_time=0.25, n=4*5)
        pump.clear()
        rgb_led.off()
        print("Calling Soroban smart contract")
        time.sleep(5)
        result = soroban_claim(
            secret_key=CLAIMANT_ADDR_SECRET_PUMPIT,
            contract_id=CONTRACT_HASH_PUMPIT,
            level=int(curr_volume)
        )
        rgb_led.color = (0, 0, 1)
        if result:
            print("Contract called successfully!")
        break
    else:
        rgb_led.color = (0, curr_volume / max_pumping_volume, 0)

pause()
