#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle interfacing with log forwarding
"""

import os
from summit_rcm.systemd_unit import (
    ActivationFailedError,
    AlreadyActiveError,
    AlreadyInactiveError,
    DeactivationFailedError,
    SystemdUnit,
)
from summit_rcm.utils import Singleton
from summit_rcm.settings import ServerConfig
from summit_rcm.definition import SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE


class LogForwardingService(SystemdUnit, metaclass=Singleton):
    """Service to handle interfacing with log forwarding"""

    def __init__(self) -> None:
        super().__init__(SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE)
        self._flag_file = f"{ServerConfig().data_dir}/log_forwarding_enabled"

    async def set_state(self, requested_state: str):
        """Set the state (active/inactive) of the log forwarding service"""

        # Read the current 'ActiveState' of the log forwarding service
        current_state = await self.get_active_state()

        if requested_state == "active":
            # Create the 'flag file' which systemd uses to determine if it should start the
            # systemd-journal-gatewayd.socket unit.
            with open(self._flag_file, "w"):
                pass

            if current_state == "active":
                # Service already active
                raise AlreadyActiveError()

            # Activate service
            if not await LogForwardingService().activate():
                raise ActivationFailedError()
        elif requested_state == "inactive":
            # Remove the 'flag file' which systemd uses to determine if it should start the
            # systemd-journal-gatewayd.socket unit.
            try:
                os.remove(self._flag_file)
            except OSError:
                # Handle the case where the file isn't already present
                pass

            if current_state == "inactive":
                # Service is already inactive
                raise AlreadyInactiveError()

            # Deactivate service
            if not await LogForwardingService().deactivate():
                raise DeactivationFailedError()
