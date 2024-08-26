#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the Datetime Command Functionality
"""
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
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            if params_dict["timestamp"]:
                await DateTimeService().set_time_manual(params_dict["timestamp"])
                return (True, "OK")
            success, datetime_str = DateTimeService().check_current_date_and_time()
            if success:
                return (True, f"+DATETIME: {datetime_str}\r\nOK")
            raise Exception(datetime_str)
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting/setting the datetime: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in DatetimeCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        params_dict["timestamp"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+DATETIME[=<timestamp>]"

    @staticmethod
    def signature() -> str:
        return DatetimeCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return DatetimeCommand.NAME
