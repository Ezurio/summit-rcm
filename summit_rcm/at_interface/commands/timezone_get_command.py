"""
File that consists of the TimezoneGet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.date_time_service import DateTimeService


class TimezoneGetCommand(Command):
    """
    AT Command to get the timezone
    """

    NAME: str = "Timezone Get"
    SIGNATURE: str = "at+tzget"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = TimezoneGetCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {TimezoneGetCommand.SIGNATURE}?\r\n",
            )
        try:
            if params_dict["scope"]:
                timezone_str = ""
                timezone_list = DateTimeService().zones
                for timezone in timezone_list:
                    timezone_str += f"+TZGET: {timezone}\r\n"
            else:
                timezone_str = f"+TZGET: {DateTimeService().local_zone}\r\n"
            return (True, f"\r\n{timezone_str}OK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting timezone: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in TimezoneGetCommand.VALID_NUM_PARAMS
        try:
            params_dict["scope"] = int(params_list[0]) if params_list[0] else 0
            if params_dict["scope"] not in (0, 1):
                raise ValueError
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+TZGET[=<scope>]\r\n"

    @staticmethod
    def signature() -> str:
        return TimezoneGetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return TimezoneGetCommand.NAME
