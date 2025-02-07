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
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)
        self._lewis.backdoor_set_on_device("crystal_pos", 5000)
        self._lewis.backdoor_set_on_device("wavelength", 500)

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
    def test_THAT_nudge_nudges(self):
        self._lewis.backdoor_set_on_device("crystal_pos", 1000)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1000)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:DIST:SP", 100)
        self.ca.assert_that_pv_is("OPO:CRYS:NUDGE:DIST", 100)

        self.ca.set_pv_value("OPO:CRYS:NUDGE:UP:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1100)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:UP:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1200)

        self.ca.set_pv_value("OPO:CRYS:NUDGE:DN:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1100)
        self.ca.set_pv_value("OPO:CRYS:NUDGE:DN:SP", 1)
        self.ca.assert_that_pv_is("OPO:CRYS:POS", 1000)

    @skip_if_recsim("need emulator")
    def test_driver_reinitializes_lvremote_on_reconnection(self):
        self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE)

        self._lewis.backdoor_set_on_device("initialized", False)
        self._lewis.backdoor_set_on_device("connected", False)
        self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.INVALID, timeout=30)

        self._lewis.backdoor_set_on_device("connected", True)

        # Should reinitialize automatically and begin reading properly again
        self.ca.assert_that_pv_alarm_is("WL", self.ca.Alarms.NONE, timeout=30)
