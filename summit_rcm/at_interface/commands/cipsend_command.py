from syslog import LOG_ERR, syslog
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService
import summit_rcm.at_interface.fsm as fsm


class CIPSENDCommand(Command):
    NAME: str = "Send IP data command"
    SIGNATURE: str = "at+cipsend"
    VALID_NUM_PARAMS: List[int] = [2]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        (valid, params_dict) = CIPSENDCommand.parse_params(params)
        if not valid:
            return (
                True,
                f"\r\nInvalid Parameters: See Usage - {CIPSENDCommand.SIGNATURE}?\r\n",
            )

        try:
            connection_status = ConnectionService().is_connection_busy(
                id=params_dict["connection_id"]
            )
            if connection_status is None:
                return (
                    True,
                    "\r\nError, Connection ID: "
                    + str(params_dict["connection_id"])
                    + " is invalid\r\n",
                )
            elif not connection_status:
                fsm.ATInterfaceFSM().dte_output("\r\n> ")

            (done, sent) = ConnectionService().send_data(
                id=params_dict["connection_id"], length=params_dict["length"]
            )

            if not done:
                return (False, "")

            if params_dict["length"] == sent:
                return (True, "\r\nOK\r\n")
            elif sent == -1:
                return (
                    True,
                    "\r\nEscape Sequence '+++' detected: Exiting Data Mode\r\n",
                )
            else:
                "\r\n Length ERROR\r\n"
        except Exception as e:
            syslog(LOG_ERR, f"CIPSEND error: {str(e)}")
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        valid = True
        params_dict = {}
        params_list = params.split(",")
        valid &= len(params_list) in CIPSENDCommand.VALID_NUM_PARAMS
        for param in params_list:
            valid &= param != ""
        if valid:
            try:
                params_dict["connection_id"] = int(params_list[0])
                params_dict["length"] = int(params_list[1])
            except Exception:
                valid = False
        return (valid, params_dict)

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPSEND=<connection id>,<length>\r\n"

    @staticmethod
    def signature() -> str:
        return CIPSENDCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return CIPSENDCommand.NAME
