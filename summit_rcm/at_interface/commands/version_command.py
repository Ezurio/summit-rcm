from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import SUMMIT_RCM_VERSION


class VersionCommand(Command):
    NAME: str = "Version"
    SIGNATURE: str = "at+ver"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = VersionCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {VersionCommand.SIGNATURE}?\r\n",
            )
        return (True, f"\r\n+VER:{SUMMIT_RCM_VERSION}\r\nOK\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in VersionCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+VER\r\n"

    @staticmethod
    def signature() -> str:
        return VersionCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return VersionCommand.NAME
