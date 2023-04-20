from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command


class CommunicationCheckCommand(Command):
    NAME: str = "Communication Check"
    SIGNATURE: str = "at"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CommunicationCheckCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CommunicationCheckCommand.SIGNATURE}?\r\n",
            )
        return (True, "\r\nOK\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_list = params.split(",")
        valid &= len(params_list) in CommunicationCheckCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, {})

    @staticmethod
    def usage() -> str:
        return "\r\nAT\r\n"

    @staticmethod
    def signature() -> str:
        return CommunicationCheckCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CommunicationCheckCommand.NAME
