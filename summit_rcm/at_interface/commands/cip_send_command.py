"""
File that consists of the CIPSend Command Functionality
"""
from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.services.connection_service import ConnectionService
import summit_rcm.at_interface.fsm as fsm


class CIPSendCommand(Command):
    """
    AT Command to send data to an IP connection
    """

    NAME: str = "Send IP data command"
    SIGNATURE: str = "at+cipsend"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPSendCommand.parse_params(params)
        if not valid:
            syslog(LOG_ERR, "Invalid Parameters")
            return (True, "ERROR")
        try:
            connection_status = ConnectionService().is_connection_busy(
                id=params_dict["connection_id"]
            )
            if connection_status is None:
                return (True, "ERROR")
            elif not connection_status:
                fsm.ATInterfaceFSM().at_output("> ", print_trailing_line_break=False)

            (done, sent) = ConnectionService().send_data(
                id=params_dict["connection_id"], length=params_dict["length"]
            )

            if not done:
                return (False, "")

            if params_dict["length"] == sent:
                return (True, "OK")
            elif sent == -1:
                syslog(LOG_ERR, "Escaping Data Mode")
                fsm.ATInterfaceFSM().at_output("\r\n", False, False)
                return (True, "")
            else:
                return (True, "ERROR")
        except Exception as exception:
            syslog(LOG_ERR, f"Error sending CIP data: {str(exception)}")
            return (True, "ERROR")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in CIPSendCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if not valid:
            return (False, {})
        try:
            params_dict["connection_id"] = int(params_list[0])
            params_dict["length"] = int(params_list[1])
        except ValueError:
            valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPSEND=<connection id>,<length>\r\n"

    @staticmethod
    def signature() -> str:
        return CIPSendCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CIPSendCommand.NAME
