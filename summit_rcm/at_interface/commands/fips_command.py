from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.fips_service import FipsService
from summit_rcm.services.system_service import SystemService


class FipsCommand(Command):
    NAME: str = "Fips"
    SIGNATURE: str = "at+fips"
    VALID_NUM_PARAMS: List[int] = [1, 2]
    VALID_STATE_VAL: List[str] = ["fips", "fips_wifi", "unset"]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FipsCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {FipsCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["state"]:
                fips_str = str(await FipsService().set_fips_state(params_dict["state"]))
                if params_dict["reboot"]:
                    await SystemService().set_power_state("reboot")
            else:
                fips_str = await FipsService().get_fips_state()
            return (True, f"\r\n+FIPS:{fips_str}\r\nOK\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in FipsCommand.VALID_NUM_PARAMS
        if valid and params_list[0].lower() in FipsCommand.VALID_STATE_VAL:
            params_dict["state"] = params_list[0]
        elif params_list[0].lower():
            valid = False
        else:
            params_dict["state"] = ""
        params_dict["reboot"] = (
            1 if (len(params_list) > 1 and params_list[1] == "1") else 0
        )
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+FIPS[=<state>[,<reboot>]]\r\n"

    @staticmethod
    def signature() -> str:
        return FipsCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FipsCommand.NAME
