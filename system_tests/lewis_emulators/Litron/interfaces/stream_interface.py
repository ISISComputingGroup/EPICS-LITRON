import struct

from lewis.adapters.stream import StreamInterface
from lewis.core.logging import has_log
from lewis.utils.byte_conversions import raw_bytes_to_int
from lewis.utils.command_builder import CmdBuilder

VI_PATH = rb"C:\instrument\dev\ibex_vis\HIFI Laser - FrontPanel.vi"


def format_lvremote_float(val: float) -> bytes:
    reply = struct.pack(">d", val)
    return len(reply).to_bytes(length=4, byteorder="big", signed=False) + reply


def format_lvremote_int(val: int) -> bytes:
    reply = int(val).to_bytes(length=4, byteorder="big", signed=False)
    return len(reply).to_bytes(length=4, byteorder="big", signed=False) + reply


@has_log
class LitronStreamInterface(StreamInterface):
    in_terminator = ""
    out_terminator = b""
    readtimeout = 10

    def __init__(self) -> None:
        super(LitronStreamInterface, self).__init__()
        # Commands that we expect via serial during normal operation
        self.commands = {
            CmdBuilder(self.any_cmd)
            .arg(r"[\x00-\xFF]+", argument_mapping=bytes)
            .eos()
            .build(return_mapping=bytes),
        }

    def any_cmd(self, cmd: bytes) -> bytes:
        if cmd == b"":
            return b""
        elif cmd == b"*IDN? ":
            if self.device.connected:
                self.device.initialized = True
            return b""

        # Device does not respond if it hasn't explicitly been
        # reinitialized (remaking connection on it's own
        # is not sufficient).
        if not self.device.connected or not self.device.initialized:
            return b""

        declared_len = raw_bytes_to_int(cmd[:4], low_bytes_first=False)
        msg = cmd[4 : 4 + declared_len]
        remainder = cmd[4 + declared_len :]

        return self.single_msg(msg) + self.any_cmd(remainder)

    def single_msg(self, msg: bytes) -> bytes:
        lvget_prefix = b"LVGET " + VI_PATH + b","
        lvput_prefix = b"LVPUT " + VI_PATH + b","

        if msg.startswith(lvget_prefix):
            return self.handle_lvget(msg[len(lvget_prefix) :])
        elif msg.startswith(lvput_prefix):
            self.handle_lvput(msg[len(lvput_prefix) :])
            return b""
        else:
            raise ValueError(f"Unrecognized message {msg}")

    def handle_lvget(self, parameter: bytes) -> bytes:
        match parameter:
            case b"btnNudgeOPOUp" | b"btnNudgeOPODown" | b"Distance":
                # Never really used by IOC - respond with dummy value
                return format_lvremote_float(0.0)
            case b"OPONudgeDistance":
                return format_lvremote_int(self._device.nudge_dist)
            case b"OPOCrystalPosition":
                return format_lvremote_int(self._device.crystal_pos)
            case b"Wavelength":
                return format_lvremote_int(self._device.wavelength)
            case _:
                raise ValueError(f"Unknown LVGET parameter: {parameter}")

    def handle_lvput(self, parameter_and_value: bytes) -> None:
        parameter, value = parameter_and_value.split(b",", maxsplit=1)

        match parameter:
            case b"btnNudgeOPOUp":
                self._device.nudge_up()
            case b"btnNudgeOPODown":
                self._device.nudge_down()
            case b"OPONudgeDistance":
                self._device.nudge_dist = raw_bytes_to_int(value, low_bytes_first=False)
            case _:
                raise ValueError(f"Unknown LVPUT parameter: {parameter}")

    def handle_error(self, request: bytes, error: str | Exception) -> None:
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error("An error occurred at request " + repr(request) + ": " + repr(error))
