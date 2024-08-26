#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the TimezoneSet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.date_time_service import DateTimeService


class TimezoneSetCommand(Command):
    """
    AT Command to set the timezone
    """

    NAME: str = "Timezone Set"
    SIGNATURE: str = "at+tzset"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = TimezoneSetCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            await DateTimeService().set_time_zone(params_dict["timezone"])
            return (True, "OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error setting timezone: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in TimezoneSetCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        params_dict["timezone"] = params_list[0]
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+TZSET=<timezone>"

    @staticmethod
    def signature() -> str:
        return TimezoneSetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return TimezoneSetCommand.NAME
