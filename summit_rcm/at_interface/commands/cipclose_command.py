from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService


@dataclass
class CIPCLOSECommand(Command):
    name = "Close IP connection"
    signature = "at+cipclose"
    valid_num_params = [1]

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPCLOSECommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CIPCLOSECommand.signature}?\r\n",
            )

        try:
            connection_id = int(params_dict["connection_id"])
            if not ConnectionService().connections[connection_id].connected:
                return (
                    True,
                    f"\r\nError, Connection ID: {str(connection_id)} is invalid\r\n",
                )
            if not ConnectionService().close_connection(id=connection_id):
                return (True, "\r\nCONNECTION CLOSE ERROR\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

        return (True, "\r\nOK\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid |= len(params_list) in CIPCLOSECommand.valid_num_params
        for param in params_list:
            valid |= param != ""
        if valid:
            try:
                params_dict["connection_id"] = int(params_list[0])
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPCLOSE=<connection id>\r\n"
