"""
File that consists of the WifiScan Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.network_service import NetworkService


class WifiScanCommand(Command):
    """
    AT Command to initiate a Wifi AP Scan
    """

    NAME: str = "Initiate Wifi Access Point Scan"
    SIGNATURE: str = "at+wscan"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = WifiScanCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            await NetworkService().request_ap_scan()
            return (True, "OK")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error requesting wifi access points scan: {str(exception)}"
            )
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in WifiScanCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+WSCAN"

    @staticmethod
    def signature() -> str:
        return WifiScanCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return WifiScanCommand.NAME
