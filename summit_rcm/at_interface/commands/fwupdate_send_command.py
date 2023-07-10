"""
File that consists of the FWUpdateSend Command Functionality
"""
from typing import List, Tuple
from syslog import LOG_ERR, syslog
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.services.firmware_update_service import (
    FirmwareUpdateService,
)
from summit_rcm.at_interface.services.at_files_service import ATFilesService
import summit_rcm.at_interface.fsm as fsm


FILE_STREAMING_BUFFER_SIZE = 4096


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
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {FWUpdateSendCommand.SIGNATURE}?\r\n",
            )
        try:
            length_remaining = (
                params_dict["length"]
                - FWUpdateSendCommand.ITERATIONS * int(FILE_STREAMING_BUFFER_SIZE)
            )
            syslog(LOG_ERR, f"Length Remaining is {length_remaining}")
            if not ATFilesService().transfer_in_process():
                fsm.ATInterfaceFSM().dte_output("\r\n> ")
            done, body, length = await ATFilesService().write_upload_body(
                length_remaining, int(FILE_STREAMING_BUFFER_SIZE)
            )
            if not done:
                syslog(LOG_ERR, "Buffer not full: Continuing")
                return (False, "")
            if length == -1:
                return (
                    True,
                    "\r\nEscape Sequence '+++' detected: Exiting Data Mode\r\n",
                )
            syslog(LOG_ERR, f"Uploading chunk #{FWUpdateSendCommand.ITERATIONS+1}")
            FirmwareUpdateService().handle_update_file_chunk(body)
            if length_remaining - length > 0:
                FWUpdateSendCommand.ITERATIONS += 1
                return (False, "")
            FWUpdateSendCommand.ITERATIONS = 0
            syslog(LOG_ERR, "Done sending fwupdate")
            return (True, f"\r\n+FWSEND: {params_dict['length']}\r\nOK\r\n")
        except Exception as exception:
            syslog(
                LOG_ERR, f"Error sending the firmware update chunk: {str(exception)}"
            )
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in FWUpdateSendCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        try:
            params_dict["length"] = int(params_list[0])
        except ValueError:
            return (False, params_dict)
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+FWSEND=<length>\r\n"

    @staticmethod
    def signature() -> str:
        return FWUpdateSendCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return FWUpdateSendCommand.NAME
