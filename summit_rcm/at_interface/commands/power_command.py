from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.system_service import SystemService


class PowerCommand(Command):
    NAME: str = "Power"
    SIGNATURE: str = "at+power"
    VALID_NUM_PARAMS: List[int] = [1]
    VALID_STATE_VAL: List[str] = ["on", "off", "suspend", "reboot"]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = PowerCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {PowerCommand.SIGNATURE}?\r\n",
            )
        try:
            await SystemService().set_power_state(params_dict["state"])
            return (True, "\r\nOK\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in PowerCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid and params_list[0].lower() in PowerCommand.VALID_STATE_VAL:
            params_dict["state"] = params_list[0]
        else:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+POWER=<state>\r\n"

    @staticmethod
    def signature() -> str:
        return PowerCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return PowerCommand.NAME
