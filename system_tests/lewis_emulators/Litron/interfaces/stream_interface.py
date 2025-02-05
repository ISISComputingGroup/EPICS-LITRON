from lewis.adapters.stream import StreamInterface
from lewis.utils.command_builder import CmdBuilder
from lewis.core.logging import has_log


@has_log
class LitronStreamInterface(StreamInterface):
    in_terminator = ""
    out_terminator = ""
    vi_path = r"C:\instrument\dev\ibex_vis\HIFI Laser - FrontPanel.vi"

    def __init__(self):
        super(LitronStreamInterface, self).__init__()
        # Commands that we expect via serial during normal operation
        self.commands = {
            CmdBuilder(self.idn).escape("*IDN? ").eos().build(),
            CmdBuilder(self.lvget).char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).escape("LVGET ").string().escape(",").string().eos().build(),
            CmdBuilder(self.lvput).char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).escape("LVPUT ").string().escape(",").string().escape(",").char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).char(ignore=True).char().eos().build(),
#            CmdBuilder(self.catch_all).arg("^.*$").build()  # Catch-all command for debugging
        }

    def handle_error(self, request, error):
        """
        If command is not recognised print and error

        Args:
            request: requested string
            error: problem

        """
        self.log.error(
            "An error occurred at request " + repr(request) + ": " + repr(error)
        )

    def catch_all(self, command):
        pass

    def idn(self):
        return "Simulated LITRON"

    def lvget(self, vi_path, control):
        return 1

    def lvput(self, vi_path, control, value):
        return

#    commands = {
#        CmdBuilder("get_crystal_position").char(ignore=True).escape(SP_COMM + "?").eos().build(),
#        CmdBuilder("nudge_up").char().escape(SP_COMM + " ").float().eos().build(),
#        CmdBuilder("get_units").char(ignore=True).escape(UNITS_COMM + "?").eos().build(),
#        CmdBuilder("set_sp").char().escape(UNITS_COMM + " ").string().eos().build(),
#        CmdBuilder("get_reading").char(ignore=True).escape(READING_COMM).eos().build(),
#    }

 