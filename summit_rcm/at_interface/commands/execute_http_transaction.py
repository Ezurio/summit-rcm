"""
File that consists of the ExecuteHTTPTransaction Command Functionality
"""

from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.utils import InProgressException
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.http_service import HTTPService


class ExecuteHTTPTransaction(Command):
    """
    AT Command to handle the execution of a configured HTTP transaction
    """
    NAME: str = "Execute HTTP Transaction"
    SIGNATURE: str = "at+httpexe"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ExecuteHTTPTransaction.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {ExecuteHTTPTransaction.SIGNATURE}?\r\n",
            )
        try:
            return_str = HTTPService().execute_http_transaction(params_dict["length"])
            return (True, f"\r\n+HTTPEXE:{return_str}\r\nOK\r\n")
        except InProgressException:
            return (False, "")
        except Exception as e:
            syslog(LOG_ERR, f"error executing http transaction {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ExecuteHTTPTransaction.VALID_NUM_PARAMS
        try:
            params_dict["length"] = int(params_list[0]) if params_list[0] else 0
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+HTTPEXE[=<length>]\r\n"

    @staticmethod
    def signature() -> str:
        return ExecuteHTTPTransaction.SIGNATURE

    @staticmethod
    def name() -> str:
        return ExecuteHTTPTransaction.NAME
