"""
File that consists of the LogGet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.logs_service import LogsService


class Types(IntEnum):
    kernel = 0
    NetworkManager = 1
    python = 2
    adaptive_ww = 3
    All = 4


class LogGetCommand(Command):
    """
    AT Command to retrieve journal log data
    """

    NAME: str = "Get Journal Log Data"
    SIGNATURE: str = "at+logget"
    VALID_NUM_PARAMS: List[int] = [3]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = LogGetCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {LogGetCommand.SIGNATURE}?\r\n",
            )
        try:
            logs_list = LogsService.get_journal_log_data(
                params_dict["type"], params_dict["priority"], params_dict["days"]
            )
            logs_str = ""
            for log in logs_list:
                logs_str += f"+LOGGET: {log}\r\n"
            return (True, f"\r\n{logs_str}OK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting journal log data: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in LogGetCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        try:
            params_dict["type"] = Types(int(params_list[0])).name
            params_dict["priority"] = int(params_list[1])
            if params_dict["priority"] not in range(0, 8):
                raise ValueError
            params_dict["days"] = int(params_list[2])
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+LOGGET=<type>,<priority>,<days>\r\n"

    @staticmethod
    def signature() -> str:
        return LogGetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return LogGetCommand.NAME
