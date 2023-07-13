"""
Module to handle interfacing with log forwarding
"""

import os
from summit_rcm.systemd_unit import SystemdUnit
from summit_rcm.utils import Singleton
from summit_rcm.definition import (
    LOG_FORWARDING_ENABLED_FLAG_FILE,
    SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE,
)

VALID_STATES = ["active", "inactive"]


class LogForwardingService(SystemdUnit, metaclass=Singleton):
    """Service to handle interfacing with log forwarding"""

    def __init__(self) -> None:
        super().__init__(SYSTEMD_JOURNAL_GATEWAYD_SOCKET_FILE)

    async def set_state(self, requested_state: str):
        """Set the state (active/inactive) of the log forwarding service"""

        # Read the current 'ActiveState' of the log forwarding service
        current_state = await self.get_active_state()

        if requested_state == "active":
            # Create the 'flag file' which systemd uses to determine if it should start the
            # systemd-journal-gatewayd.socket unit.
            with open(LOG_FORWARDING_ENABLED_FLAG_FILE, "w"):
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
                os.remove(LOG_FORWARDING_ENABLED_FLAG_FILE)
            except OSError:
                # Handle the case where the file isn't already present
                pass

            if current_state == "inactive":
                # Service is already inactive
                raise AlreadyInactiveError()

            # Deactivate service
            if not await LogForwardingService().deactivate():
                raise DeactivationFailedError()


class AlreadyActiveError(Exception):
    """
    Custom error class for when a user requests to activate the log forwarding service, but it's
    already active.
    """


class AlreadyInactiveError(Exception):
    """
    Custom error class for when a user requests to deactivate the log forwarding service, but it's
    already inactive.
    """


class ActivationFailedError(Exception):
    """
    Custom error class for when a user requests to activate the log forwarding service, but the
    activation fails
    """


class DeactivationFailedError(Exception):
    """
    Custom error class for when a user requests to deactivate the log forwarding service, but the
    deactivation fails
    """
