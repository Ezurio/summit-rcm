#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
File that consists of the FWUpdateSend Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.firmware_update_service import (
    FirmwareUpdateService,
    SummitRCMUpdateStatus,
)
from summit_rcm.at_interface.services.at_files_service import ATFilesService
import summit_rcm.at_interface.fsm as fsm


FILE_STREAMING_BUFFER_SIZE = 1024 * 128


class FWUpdateSendCommand(Command):
    """
    AT Command to send a firmware update chunk
    """

    NAME: str = "Send a firmware update chunk"
    SIGNATURE: str = "at+fwsend"
    VALID_NUM_PARAMS: List[int] = [1]
    DEVICE_TYPE: str = ""
    ITERATIONS: int = 0

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = FWUpdateSendCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            status, _ = FirmwareUpdateService().get_update_status()
            if status != SummitRCMUpdateStatus.UPDATING:
                raise Exception("Not updating")
            length_remaining = params_dict[
                "length"
            ] - FWUpdateSendCommand.ITERATIONS * int(FILE_STREAMING_BUFFER_SIZE)
            if not ATFilesService().transfer_in_process():
                fsm.ATInterfaceFSM().at_output("> ", print_trailing_line_break=False)
            done, body, length = await ATFilesService().write_upload_body(
                length_remaining, int(FILE_STREAMING_BUFFER_SIZE)
            )
            if not done:
                return (False, "")
            if length == -1:
                syslog(LOG_ERR, "Escaping Data Mode")
                fsm.ATInterfaceFSM().at_output("\r\n", False, False)
                return (True, "")
            FirmwareUpdateService().handle_update_file_chunk(body)
            if length_remaining - length > 0:
                FWUpdateSendCommand.ITERATIONS += 1
                return (False, "")
            FWUpdateSendCommand.ITERATIONS = 0
            FirmwareUpdateService().cancel_update()
            return (True, f"+FWSEND: {params_dict['length']}\r\nOK")
        except Exception as exception:
            syslog(LOG_ERR, f"Error sending the firmware update: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FWUpdateSendCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["length"] = int(params_list[0])
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "AT+FWSEND=<length>"

    @staticmethod
    def signature() -> str:
        return FWUpdateSendCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FWUpdateSendCommand.NAME
