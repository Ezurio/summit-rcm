"""
File that consists of the AWMScan Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.awm.awm_config_service import AWMConfigService, ConfigFileNotFoundError


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
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {AWMScanCommand.SIGNATURE}?\r\n",
            )
        try:
            enabled = params_dict["enabled"]
            if enabled == "":
                awm_scan_str = AWMConfigService().get_scan_attempts()
                return (True, f"\r\n+AWMSCAN: {awm_scan_str}\r\nOK\r\n")
            AWMConfigService().set_scan_attempts(enabled)
            return (True, "\r\nOK\r\n")
        except ConfigFileNotFoundError:
            syslog(LOG_ERR, "AWM Config File Not Found")
            if params_dict["enabled"] == "":
                return (True, "\r\n+AWMSCAN: 1\r\nOK\r\n")
            return (True, "\r\nERROR\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error getting/setting AWM geolocation scanning: {str(exception)}"
            )
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in AWMScanCommand.VALID_NUM_PARAMS
        if params_list[0] == "":
            params_dict["enabled"] = ""
        else:
            try:
                params_dict["enabled"] = int(params_list[0])
                if params_dict["enabled"] not in (0, 1):
                    raise ValueError
            except ValueError:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+AWMSCAN[=<enabled>]\r\n"

    @staticmethod
    def signature() -> str:
        return AWMScanCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return AWMScanCommand.NAME
