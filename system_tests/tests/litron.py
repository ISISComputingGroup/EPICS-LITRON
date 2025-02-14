import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim

DEVICE_PREFIX = "LITRON_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LITRON"),
        "macros": {"IPADDR": "127.0.0.1", "VI_PATH": "C:/instrument/dev/ibex_vis/"},
        "emulator": "Litron",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]


class LitronTests(unittest.TestCase):
    """
    Tests for the Litron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Litron", DEVICE_PREFIX)
        self.ca = ChannelAccess(
            device_prefix=DEVICE_PREFIX, default_timeout=15, default_wait_time=0.0
        )

    def test_THAT_nudge_changes_distance(self):
        self.ca.assert_setting_setpoint_sets_readback(1, "OPO:CRYS:NUDGE:DIST")

    @skip_if_recsim("requires backdoor")
    def test_can_read_crystal_pos(self):
        self._lewis.backdoor_set_on_device("crystal_pos", 1234)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1234)

    @skip_if_recsim("requires backdoor")
    def test_can_read_wavelength(self):
        self._lewis.backdoor_set_on_device("wavelength", 4321)
        self.ca.assert_that_pv_is("WL", 4321)

    @skip_if_recsim("requires backdoor")
    def test_THAT_nudge_nudges_crystal_position(self):
        self._lewis.backdoor_set_on_device("crystal_pos", 1000)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1000)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:DIST:SP", 100)
        self.ca.assert_that_pv_is("OPO:CRYS:NUDGE:DIST", 100)

        # Nudge up twice
        self.ca.set_pv_value("OPO:CRYS:NUDGE:UP:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1100)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:UP:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1200)

        # Nudge back down twice
        self.ca.set_pv_value("OPO:CRYS:NUDGE:DN:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1100)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:DN:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1000)

    @skip_if_recsim("requires backdoor")
    def test_driver_reinitializes_lvremote_on_reconnection_from_failed_reply(self):
        self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE)

        self._lewis.backdoor_set_on_device("initialized", False)
        with self._lewis.backdoor_simulate_disconnected_device():  # Failure to reply
            self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.INVALID, timeout=30)

        # Should reinitialize automatically and begin reading properly again
        self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE, timeout=30)

    # @skip_if_recsim("requires backdoor")
    # def test_driver_reinitializes_lvremote_on_reconnection_from_closed_tcp_connection(self):
    #     self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE)
    #
    #     # Closes TCP connection - looks different to EPICS, compared to an open connection
    #     # that doesn't reply.
    #     self._lewis.backdoor_command(["interface", "disconnect"])
    #
    #     self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.INVALID, timeout=30)
    #     self._lewis.backdoor_set_on_device("initialized", False)
    #     sleep(5)  # Don't reconnect *immediately* as that's a bit of a special case.
    #
    #     self._lewis.backdoor_command(["interface", "connect"])
    #     self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE, timeout=30)
