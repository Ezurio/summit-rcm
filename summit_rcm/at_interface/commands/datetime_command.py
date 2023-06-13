"""
File that consists of the Datetime Command Functionality
"""
from json import dumps
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.date_time_service import DateTimeService


class DatetimeCommand(Command):
    """
    AT Command to get/set the datetime
    """
    NAME: str = "Datetime"
    SIGNATURE: str = "at+datetime"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = DatetimeCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {DatetimeCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["timestamp"]:
                await DateTimeService().set_time_manual(params_dict["timestamp"])
                return (True, "\r\nOK\r\n")
            success, datetime_str = DateTimeService().check_current_date_and_time()
            if success:
                return (True, f"\r\n+DATETIME:{datetime_str}\r\nOK\r\n")
            raise Exception(datetime_str)
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting/setting the datetime: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in DatetimeCommand.VALID_NUM_PARAMS
        params_dict["timestamp"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+DATETIME[=<timestamp>]\r\n"

    @staticmethod
    def signature() -> str:
        return DatetimeCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return DatetimeCommand.NAME
