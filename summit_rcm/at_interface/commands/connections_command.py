from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command


class ConnectionsCommand(Command):
    NAME: str = "Connections"
    SIGNATURE: str = "at+lcon"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionsCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ConnectionsCommand.SIGNATURE}?\r\n",
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
        valid &= len(params_list) in ConnectionsCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+LCON\r\n"

    @staticmethod
    def signature() -> str:
        return ConnectionsCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ConnectionsCommand.NAME
