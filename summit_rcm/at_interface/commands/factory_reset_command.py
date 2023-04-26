from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.system_service import SystemService


class FactoryResetCommand(Command):
    NAME: str = "Factory Reset"
    SIGNATURE: str = "at+factreset"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FactoryResetCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {FactoryResetCommand.SIGNATURE}?\r\n",
            )
        try:
            return_str = await SystemService().initiate_factory_reset()
            if return_str != 0:
                raise Exception
            if params_dict["reboot"]:
                await SystemService().set_power_state("reboot")
            return (True, f"\r\n+FACTRESET:{return_str}\r\nOK\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in FactoryResetCommand.VALID_NUM_PARAMS
        params_dict["reboot"] = 1 if params_list[0] == "1" else 0
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+FACTRESET[=<reboot>]\r\n"

    @staticmethod
    def signature() -> str:
        return FactoryResetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FactoryResetCommand.NAME
