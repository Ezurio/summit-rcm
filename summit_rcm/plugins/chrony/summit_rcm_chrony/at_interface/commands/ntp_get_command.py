#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the NTPGet Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm_chrony.services.ntp_service import ChronyNTPService


class Types(IntEnum):
    ALL_CHRONY_SOURCES = -1
    STATIC_CHRONY_SOURCES = 0
    CURRENT_CHRONY_SOURCES = 1


class NTPGetCommand(Command):
    """
    AT Command to get NTP Sources
    """

    NAME: str = "Get NTP Sources"
    SIGNATURE: str = "at+ntpget"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NTPGetCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            sources_str = ""
            if params_dict["scope"] == Types.ALL_CHRONY_SOURCES:
                sources_list = await ChronyNTPService.chrony_get_sources()
                for source in sources_list:
                    sources_str += f"+NTPGET: {source['address']},{source['type']}\r\n"
            elif params_dict["scope"] == Types.STATIC_CHRONY_SOURCES:
                sources_list = await ChronyNTPService.chrony_get_static_sources()
                for source in sources_list:
                    sources_str += f"+NTPGET: {source}\r\n"
            else:
                sources_list = await ChronyNTPService.chrony_get_current_sources()
                for source in sources_list:
                    sources_str += f"+NTPGET: {source}\r\n"
            return (True, f"{sources_str}OK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error getting NTP Sources: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in NTPGetCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["scope"] = (
                Types(int(params_list[0])) if params_list[0] else Types(-1)
            )
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+NTPGET[=<scope>]"

    @staticmethod
    def signature() -> str:
        return NTPGetCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NTPGetCommand.NAME
