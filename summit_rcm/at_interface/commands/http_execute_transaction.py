#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the HTTPExecuteTransaction Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.utils import InProgressException
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.http_service import HTTPService
import summit_rcm.at_interface.fsm as fsm


class HTTPExecuteTransaction(Command):
    """
    AT Command to handle the execution of a configured HTTP transaction
    """

    NAME: str = "Execute HTTP Transaction"
    SIGNATURE: str = "at+httpexe"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = HTTPExecuteTransaction.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            return_str, length = HTTPService().execute_http_transaction(
                params_dict["length"]
            )
            if length == -1:
                syslog(LOG_ERR, "Escaping Data Mode")
                fsm.ATInterfaceFSM().at_output("\r\n", False, False)
                return (True, "")
            return (True, f"+HTTPEXE: {return_str}\r\nOK")
        except InProgressException:
            return (False, "")
        except Exception as exception:
            syslog(LOG_ERR, f"Error executing http transaction: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in HTTPExecuteTransaction.VALID_NUM_PARAMS
        if not valid:
            return (False, {})
        try:
            params_dict["length"] = int(params_list[0]) if params_list[0] else 0
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+HTTPEXE[=<length>]"

    @staticmethod
    def signature() -> str:
        return HTTPExecuteTransaction.SIGNATURE

    @staticmethod
    def name() -> str:
        return HTTPExecuteTransaction.NAME
