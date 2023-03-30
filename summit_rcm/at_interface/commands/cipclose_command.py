from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService


@dataclass
class CIPCLOSECommand(Command):
    name = "Close IP connection"
    signature = "at+cipclose"

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        params_list = params.split(",")
        num_params = len(params_list)
        if num_params != 1:
            return (True, "\r\nERROR\r\n")

        try:
            connection_id = int(params_list[0])

            if not ConnectionService().close_connection(id=connection_id):
                return (True, "\r\nERROR\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

        return (True, "\r\nOK\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPCLOSE=<connection id>\r\n"
