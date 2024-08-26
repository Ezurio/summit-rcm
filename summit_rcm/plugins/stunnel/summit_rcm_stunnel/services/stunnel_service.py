#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support stunnel configuration
"""

import re
import os

try:
    import aiofiles
except ImportError as error:
    # Ignore the error if the aiofiles module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
from summit_rcm.systemd_unit import (
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
    SystemdUnit,
)
from summit_rcm.utils import Singleton

STUNNEL_SERVICE_FILE = "stunnel.service"
STUNNEL_CONF_FILE = "/etc/stunnel/stunnel.conf"
STUNNEL_CONF_FIPS_ENABLED = "fips = yes"
STUNNEL_CONF_FIPS_REG_EXP = r"fips\s*=\s*"


class StunnelService(SystemdUnit, metaclass=Singleton):
    """
    Service to handle stunnel configuration
    """

    def __init__(self) -> None:
        super().__init__(STUNNEL_SERVICE_FILE)

    @staticmethod
    async def configure_fips(enabled: bool):
        """
        Update the stunnel configuration file to enable/disable FIPS support according to the given
        parameter (enabled).
        """
        new_content = []
        async with aiofiles.open(STUNNEL_CONF_FILE, "r") as stunnel_conf_file:
            for line in await stunnel_conf_file.readlines():
                if re.search(STUNNEL_CONF_FIPS_REG_EXP, line):
                    # Found the target line
                    new_content.append(
                        f"{'' if enabled else ';'}{STUNNEL_CONF_FIPS_ENABLED}\n"
                    )
                else:
                    new_content.append(line)
        async with aiofiles.open(STUNNEL_CONF_FILE, "w") as stunnel_conf_file:
            await stunnel_conf_file.writelines(new_content)

    async def set_state(self, requested_state: str):
        """Set the state (active/inactive) of the stunnel service"""

        # Read the current 'ActiveState' of the stunnel service
        current_state = await self.get_active_state()

        if requested_state == "active":
            if current_state == "active":
                # Service already active
                raise AlreadyActiveError()

            # Activate service
            if not await self.activate():
                raise ActivationFailedError()
        elif requested_state == "inactive":
            if current_state == "inactive":
                # Service is already inactive
                raise AlreadyInactiveError()

            # Deactivate service
            if not await self.deactivate():
                raise DeactivationFailedError()
