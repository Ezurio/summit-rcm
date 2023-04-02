from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command


@dataclass
class ConnectionsCommand(Command):
    name = "Connections"
    signature = "at+lcon"
    valid_num_params = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionsCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ConnectionsCommand.signature}?\r\n",
            )
        try:
            connections_str = ""
            return (True, "\r\n" + connections_str + "\r\n")
        except Exception:
            return (True, "\r\nError\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ConnectionsCommand.valid_num_params
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+LCON\r\n"
