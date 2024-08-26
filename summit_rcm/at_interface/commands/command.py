#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from typing import Tuple


class Command:
    @staticmethod
    async def execute(params: str) -> Tuple[bool, str]:
        """
        Function which runs the actual logic of the command. Return type is a tuple in the form
        (done, response)
        """
        pass

    @staticmethod
    def parse_params(params: str) -> Tuple[bool, dict]:
        """
        Function which runs the parameters through a parsing function. Returns a dictionary
        consisting of parameter names and values.
        """
        pass

    @staticmethod
    def usage() -> str:
        """
        Returns the expected usage of the command
        """
        pass

    @staticmethod
    def signature() -> str:
        return ""

    @staticmethod
    def name() -> str:
        return ""
