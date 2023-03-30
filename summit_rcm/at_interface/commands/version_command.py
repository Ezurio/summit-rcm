from dataclasses import dataclass
from typing import Tuple
from summit_rcm.at_interface.commands.command import Command
from summit_rcm.definition import SUMMIT_RCM_VERSION


@dataclass
class VersionCommand(Command):
    name = "Version"
    signature = "at+ver"

    @staticmethod
    def execute(params: str) -> Tuple[bool, str]:
        if params != "":
            return (True, "\r\nERROR\r\n")

        return (True, f"\r\n{SUMMIT_RCM_VERSION}\r\nOK\r\n")

    @staticmethod
    def usage() -> str:
        return "\r\nAT+VER\r\n"
