"""
File that consists of the AWMScan Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm_awm.services.awm_config_service import (
    AWMConfigService,
    ConfigFileNotFoundError,
)


class AWMScanCommand(Command):
    """
    AT Command to enable/disable AWM Geolocation Scanning
    """

    NAME: str = "Enable/disable AWM Geolocation Scanning"
    SIGNATURE: str = "at+awmscan"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = AWMScanCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            enabled = params_dict["enabled"]
            if enabled == "":
                awm_scan_str = AWMConfigService().get_scan_attempts()
                return (True, f"+AWMSCAN: {awm_scan_str}\r\nOK")
            AWMConfigService().set_scan_attempts(enabled)
            return (True, "OK")
        except ConfigFileNotFoundError:
            if params_dict["enabled"] == "":
                return (True, "+AWMSCAN: 1\r\nOK")
            syslog(LOG_ERR, "AWM Config File Not Found")
            return (True, "ERROR")
        except Exception as exception:
            syslog(
                LOG_ERR,
                f"Error getting/setting AWM geolocation scanning: {str(exception)}",
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in AWMScanCommand.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["enabled"] = int(params_list[0]) if params_list[0] else ""
            if params_dict["enabled"] not in (0, 1, ""):
                raise ValueError
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+AWMSCAN[=<enabled>]"

    @staticmethod
    def signature() -> str:
        return AWMScanCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return AWMScanCommand.NAME
