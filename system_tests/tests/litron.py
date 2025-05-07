import unittest
from typing import List

from utils.channel_access import ChannelAccess
from utils.ioc_launcher import get_default_ioc_dir
from utils.test_modes import TestModes
from utils.testing import get_running_lewis_and_ioc, skip_if_recsim, skip_if_devsim

DEVICE_PREFIX = "LITRON_01"
STALE_TIME = 5

IOCS = [
    {
        "name": DEVICE_PREFIX,
        "directory": get_default_ioc_dir("LITRON"),
        "macros": {
                    "IPADDR": "127.0.0.1", 
                   "VI_PATH": "C:/instrument/dev/ibex_vis/", 
                   "BUFFER_SIZE":f"{STALE_TIME}"
                   },
        "emulator": "Litron",
    },
]


TEST_MODES = [TestModes.RECSIM, TestModes.DEVSIM]

def _contains_check(array, check_vals):
    for val in check_vals:
        if not val in array:
            return False
    return True

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
        self.ca.assert_that_pv_is_number("WL", 4321, 0.1)

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
        
    @skip_if_devsim("Requires sim record")
    def test_THAT_buffer_corectly_handles_WL_input(self):
        # setup test functions
        empty_buffer = [0.0] * STALE_TIME
        
        def _check_empty_and_1(array):
            return _contains_check(array, [1.0] + empty_buffer[1:])
        
        def _check_empty_and_both(array):
            return _contains_check(array, [1.0, -1.0] + empty_buffer[2:])
        
        
        # Make sure the buffer is empty.
        self.ca.set_pv_value("STALE_CHECK:BUFFER.RES", 1)
        self.ca.set_pv_value("STALE_CHECK:BUFFER:MAX.RES", 1)
        self.ca.set_pv_value("STALE_CHECK:BUFFER:MIN.RES", 1)
        
        
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER", empty_buffer)
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER:MAX", 0)
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER:MIN", 0)
        self.ca.assert_that_pv_is("STALE", "Stale")
        
        self.ca.set_pv_value("SIM:WL", 1)
        
        
        
        self.ca.assert_that_pv_value_causes_func_to_return_true("STALE_CHECK:BUFFER", _check_empty_and_1)
        self.ca.set_pv_value("SIM:WL", -1)
        self.ca.assert_that_pv_value_causes_func_to_return_true("STALE_CHECK:BUFFER", _check_empty_and_both)
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER:MAX", 1)
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER:MIN", -1)
        self.ca.assert_that_pv_is("STALE", "Good")
        
    
    @skip_if_recsim("requires backdoor and noise")
    def test_THAT_value_staleness_is_detected_WHEN_hardware_is_not_connected_to_vi(self):
        empty_buffer = [0.0] * STALE_TIME
        
        # Buffer not stale when noise is enabled (default) on emulator
        self.ca.assert_that_pv_is("STALE", "Good")
        self.ca.assert_that_pv_is_not("STALE_CHECK:BUFFER", [0.0] * STALE_TIME)
        
        # Buffer becomes stale after STALE_TIME has passed seconds after hardware disconnect
        self._lewis.backdoor_set_on_device("hardware_connected", False)
        self.ca.assert_that_pv_is("WL", 0)
        self.ca.assert_that_pv_is("STALE_CHECK:BUFFER", empty_buffer, timeout=25)
        self.ca.assert_that_pv_is("STALE", "Stale", timeout=STALE_TIME)
        self.ca.assert_that_pv_alarm_is("STALE", self.ca.Alarms.MAJOR, timeout=STALE_TIME)

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
