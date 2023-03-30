from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService


@dataclass
class CIPSTARTCommand(Command):
    name = "Start IP connection"
    signature = "at+cipstart"

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        params_list = params.split(",")
        num_params = len(params_list)
        if num_params < 4 or num_params > 5:
            return (True, "\r\nERROR\r\n")

        connection_id = int(params_list[0])
        type = params_list[1]
        remote_ip = params_list[2]
        remote_port = params_list[3]
        enable_keepalive = params_list[4] if num_params == 5 else False

        connection_type = ConnectionService.parse_connection_type(type)
        if connection_type is None:
            return (True, "\r\nERROR\r\n")

        if ConnectionService().start_connection(
            id=connection_id,
            type=connection_type,
            addr=remote_ip,
            port=remote_port,
            enable_keepalve=enable_keepalive,
        ):
            return (True, "\r\nOK\r\n")
        else:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPSTART=<connection id>,<type>,<remote IP>,<remote port>[,<enable keepalive>]\r\n"
