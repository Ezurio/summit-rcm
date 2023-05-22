"""
File that consists of the CIPStart Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.connection_service import ConnectionService


class Types(IntEnum):
    tcp = 0
    udp = 1
    ssl = 2


class CIPStartCommand(Command):
    """
    AT Command to start an IP connection
    """

    NAME: str = "Start IP connection"
    SIGNATURE: str = "at+cipstart"
    VALID_NUM_PARAMS: List[int] = [5]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPStartCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")

        if await ConnectionService().start_connection(
            id=params_dict["connection_id"],
            type=params_dict["type"],
            addr=params_dict["remote_ip"],
            port=params_dict["remote_port"],
            keepalive=params_dict["keepalive"],
        ):
            return (True, "OK")
        else:
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        given_num_param = len(params_list)
        valid &= given_num_param in CIPStartCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["connection_id"] = int(params_list[0])
            params_dict["type"] = Types(int(params_list[1])).name
            params_dict["remote_ip"] = params_list[2]
            params_dict["remote_port"] = params_list[3]
            params_dict["keepalive"] = int(params_list[4]) if params_list[4] else 0
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return (
            "AT+CIPSTART=<connection id>,<type>,<remote IP>,"
            "<remote port>[,<keepalive>]"
        )

    @staticmethod
    def signature() -> str:
        return CIPStartCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CIPStartCommand.NAME
