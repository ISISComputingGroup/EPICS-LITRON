from collections import OrderedDict
from typing import Callable
from random import uniform

from lewis.core.statemachine import State
from lewis.devices import StateMachineDevice

from .states import DefaultState


class SimulatedLitron(StateMachineDevice):
    def _initialize_data(self) -> None:
        """
        Initialize all of the device's attributes.
        """

        # Whether the hardware is "connected"
        self.connected = True

        # Whether the hardware and the vi are interacting, for the purpose of stale values
        self.hardware_connected = True
        # Whether the LVRemote software has been reinitialized
        # by sending *IDN? since the last disconnection
        # (if not, it will not reply)
        self.initialized = True

        self.crystal_pos = 5000
        self.nudge_dist = 0
        self.wavelength = 0

    def nudge_up(self) -> None:
        self.crystal_pos += self.nudge_dist

    def nudge_down(self) -> None:
        self.crystal_pos -= self.nudge_dist
        
    def get_wavelength(self) -> float:
        if self.hardware_connected:
            return self.wavelength + uniform(-0.05, 0.05)
        else:
            return self.wavelength
            

    def _get_state_handlers(self) -> dict[str, State]:
        return {
            "default": DefaultState(),
        }

    def _get_initial_state(self) -> str:
        return "default"

    def _get_transition_handlers(self) -> OrderedDict[tuple[str, str], Callable[[], bool]]:
        return OrderedDict([])
