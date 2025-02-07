from collections import OrderedDict
from typing import Callable

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

        # Whether the LVRemote software has been reinitialized since the last disconnection
        self.initialized = True

        self.crystal_pos = 5000
        self.nudge_dist = 0
        self.wavelength = 0

    def nudge_up(self) -> None:
        self.crystal_pos += self.nudge_dist

    def nudge_down(self) -> None:
        self.crystal_pos -= self.nudge_dist

    def _get_state_handlers(self) -> dict[str, State]:
        return {
            "default": DefaultState(),
        }

    def _get_initial_state(self) -> str:
        return "default"

    def _get_transition_handlers(self) -> OrderedDict[tuple[str, str], Callable[[], bool]]:
        return OrderedDict([])
