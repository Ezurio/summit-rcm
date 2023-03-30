from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command


@dataclass
class CommunicationCheckCommand(Command):
    name = "Communication Check"
    signature = "at"
    valid_num_params = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CommunicationCheckCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CommunicationCheckCommand.signature}?\r\n",
            )
        return (True, "\r\nOK\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_list = params.split(",")
        valid |= len(params_list) in CommunicationCheckCommand.valid_num_params
        for param in params_list:
            valid |= param != ""
        return (valid, {})

    @staticmethod
    def usage() -> str:
        return "\r\nAT\r\n"
