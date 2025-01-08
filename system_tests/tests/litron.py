import unittest

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc


DEVICE_PREFIX = "LITRON_01"


IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LITRON"),
        "macros": {"IPADDR": "127.0.0.1", "VI_PATH": "C:/instrument/dev/ibex_vis/"},
        "emulator": "Litron",
    },
]


TEST_MODES = [TestModes.RECSIM]


class LitronTests(unittest.TestCase):
    """
    Tests for the Litron IOC.
    """

    def setUp(self):
        self._lewis, self._ioc = get_running_lewis_and_ioc("Litron", DEVICE_PREFIX)
        self.ca = ChannelAccess(device_prefix=DEVICE_PREFIX)

    def test_THAT_nudge_changes_distance(self):
        self.ca.assert_setting_setpoint_sets_readback(
            1, "OPO:CRYS:NUDGE:DIST", "OPO:CRYS:NUDGE:DIST:SP"
        )

    def test_THAT_nudge_up_changes(self):
        self.ca.assert_setting_setpoint_sets_readback(
            1, "OPO:CRYS:NUDGE:UP", "OPO:CRYS:NUDGE:UP:SP"
        )

    def test_THAT_nudge_down_changes_down(self):
        self.ca.assert_setting_setpoint_sets_readback(
            1, "OPO:CRYS:NUDGE:DN", "OPO:CRYS:NUDGE:DN:SP"
        )
