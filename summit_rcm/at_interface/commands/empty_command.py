"""
File that consists of the Empty Command Functionality
"""
from typing import List, Tuple
from summit_rcm.at_interface.commands.command import Command
import summit_rcm.at_interface.fsm as fsm


class EmptyCommand(Command):
    """
    AT Command that returns a CRLF
    """

    NAME: str = "Empty"
    SIGNATURE: str = ""
    VALID_NUM_PARAMS: List[int] = [0]

    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        fsm.ATInterfaceFSM().at_output("\r\n", False, False)
        return (True, "")

    @staticmethod
    def usage() -> str:
        return ""

    @staticmethod
    def signature() -> str:
        return EmptyCommand.SIGNATURE

    @staticmethod
    def name() -> str:
        return EmptyCommand.NAME
