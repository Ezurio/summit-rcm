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


class Priorities(IntEnum):
    LOG_EMERG = 0
    LOG_ALERT = 1
    LOG_CRIT = 2
    LOG_ERR = 3
    LOG_WARNING = 4
    LOG_NOTICE = 5
    LOG_INFO = 6
    LOG_DEBUG = 7


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
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "\r\nERROR\r\n")
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
        if not valid:
            return (False, {})
        try:
            params_dict["type"] = Types(int(params_list[0])).name
            params_dict["priority"] = Priorities(int(params_list[1])).value
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
