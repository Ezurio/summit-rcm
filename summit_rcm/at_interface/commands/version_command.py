from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import SUMMIT_RCM_VERSION


@dataclass
class VersionCommand(Command):
    name = "Version"
    signature = "at+ver"
    valid_num_params = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = VersionCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {VersionCommand.signature}?\r\n",
            )
        return (True, f"\r\n{SUMMIT_RCM_VERSION}\r\nOK\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid |= len(params_list) in VersionCommand.valid_num_params
        for param in params_list:
            valid |= param != ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+VER\r\n"
