from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.at_interface.connection_service import ConnectionService

import summit_rcm.at_interface.fsm as fsm


@dataclass
class CIPSENDCommand(Command):
    name = "Send IP data command"
    signature = "at+cipsend"

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        params_list = params.split(",")
        num_params = len(params_list)
        if num_params != 2:
            return (True, "\r\nERROR\r\n")

        try:
            connection_id = int(params_list[0])
            length = int(params_list[1])

            if not ConnectionService().is_connection_busy(id=connection_id):
                fsm.ATCommandStateMachine().dte_output("\r\n> ")

            (done, sent) = ConnectionService().send_data(
                id=connection_id, length=length
            )

            if not done:
                return (False, "")

            return (True, "\r\nOK\r\n" if length == sent else "\r\nERROR\r\n")
        except Exception:
            return (True, "\r\nERROR\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\nAT+CIPSEND=<connection id>,length\r\n"
