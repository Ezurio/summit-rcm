#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle FIPS configuration
"""

import asyncio
from syslog import LOG_ERR, syslog
from summit_rcm.utils import Singleton

VALID_FIPS_STATES = ["fips", "fips_wifi", "unset"]
FIPS_SCRIPT = "/usr/bin/fips-set"


class FipsService(metaclass=Singleton):
    """
    Service to handle FIPS configuration
    """

    async def set_fips_state(self, value: str) -> bool:
        """
        Configure the desired FIPS state for the module (reboot required) and return a boolean
        indicating success. Possible values are:
        - fips
        - fips_wifi
        - unset
        """
        try:
            if value not in ["fips", "fips_wifi", "unset"]:
                raise f"invalid input parameter {str(value)}"

            proc = await asyncio.create_subprocess_exec(
                *[FIPS_SCRIPT, value],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.decode("utf-8").strip())
        except FileNotFoundError:
            return False
        except Exception as exception:
            syslog(LOG_ERR, f"set_fips_state exception: {str(exception)}")
            return False

        return True

    async def get_fips_state(self) -> str:
        """
        Retrieve the current FIPS state for the module. Possible values are:
        - fips
        - fips_wifi
        - unset
        - unsupported
        - unknown
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                *[FIPS_SCRIPT, "status"],
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode != 0:
                raise Exception(stderr.decode("utf-8").strip())
            status = stdout.decode("utf-8").strip()
            return status if status in VALID_FIPS_STATES else "unknown"
        except FileNotFoundError:
            return "unsupported"
        except Exception as exception:
            syslog(LOG_ERR, f"get_fips_state exception: {str(exception)}")
            return "unknown"


class FipsUnsupportedError(Exception):
    """Custom error class for when Fips is not supported"""
