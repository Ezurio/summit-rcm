#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the ATEchoEnable Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
import summit_rcm.at_interface.fsm as fsm


class ATEchoEnableCommand(Command):
    """
    AT Command to enable the AT Interface's serial echo
    """

    NAME: str = "Enable AT Serial Echo"
    SIGNATURE: str = "ate1"
    VALID_NUM_PARAMS: List[int] = [1]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = ATEchoEnableCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        fsm.ATInterfaceFSM().enable_echo(True)
        return (True, "OK")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in ATEchoEnableCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param == ""
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "ATE1"

    @staticmethod
    def signature() -> str:
        return ATEchoEnableCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return ATEchoEnableCommand.NAME
