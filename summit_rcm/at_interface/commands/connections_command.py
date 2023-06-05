from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class ConnectionsCommand(Command):
    NAME: str = "Connections"
    SIGNATURE: str = "at+lcon"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ConnectionsCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ConnectionsCommand.SIGNATURE}?\r\n",
            )
        try:
            connections_str = ""
            connections_list = await NetworkService().get_all_connection_profiles()
            for connection in connections_list:
                connection['activated'] = 1 if connection['activated'] else 0
                connections_str += f"{connection['uuid']}:{connection['id']},{connection['activated']}\r\n"
            connections_str = connections_str[:-2]
            return (True, f"\r\n+LCON:{connections_str}\r\nOK\r\n")
        except Exception as e:
            syslog(LOG_ERR, f"Error getting connection {str(e)}")
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
