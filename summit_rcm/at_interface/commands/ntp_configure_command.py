"""
File that consists of the NTPConfigure Command Functionality
"""
from typing import Tuple
from syslog import LOG_ERR, syslog
from enum import IntEnum
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.chrony.ntp_service import ChronyNTPService


class Types(IntEnum):
    addSource = 0
    removeSource = 1
    overrideSources = 2


class NTPConfigureCommand(Command):
    """
    AT Command to configure NTP Sources
    """

    NAME: str = "Configure NTP"
    SIGNATURE: str = "at+ntpconf"
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = NTPConfigureCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {NTPConfigureCommand.SIGNATURE}?\r\n",
            )
        try:
            await ChronyNTPService.chrony_configure_sources(
                params_dict["command"], params_dict["sources"]
            )
            return (True, "\r\nOK\r\n")
        except Exception as exception:
            syslog(LOG_ERR, f"Error configuring NTP Sources: {str(exception)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) > 1
        for param in params_list:
            valid &= param != ""
        try:
            params_dict["command"] = Types(int(params_list[0])).name
            del params_list[0]
            sources_list = []
            for param in params_list:
                param = param.strip('[]')
                param = param.strip("'")
                param = param.strip('"')
                if param != "":
                    sources_list.append(param)
            params_dict["sources"] = sources_list
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+NTPCONF=<command>,<sources>\r\n"

    @staticmethod
    def signature() -> str:
        return NTPConfigureCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return NTPConfigureCommand.NAME
