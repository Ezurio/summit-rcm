#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
from syslog import syslog, LOG_ERR
from summit_rcm.settings import SystemSettingsManage


class UnauthenticatedService:
    """
    Service for configuring the Allow Unauthenticated Reset Reboot Plugin
    """
    def __init__(self) -> None:
        self._allowed: bool = SystemSettingsManage.getBool(
            "AllowUnauthenticatedRebootReset", False
        )

    def get_allow_unauthenticated_enabled(self) -> bool:
        """Get the Allow Unauthenticated Enabled Value"""
        return self._allowed

    def set_allow_unauthenticated_enabled(self, enabled: bool) -> bool:
        """Set the Allow Unauthenticated Enabled Value"""
        try:
            SystemSettingsManage.update_persistent(
                "AllowUnauthenticatedRebootReset", str(enabled)
            )
            return True
        except Exception as exception:
            syslog(LOG_ERR, f"Error updating unauthenticated enabled: {str(exception)}")
            return False
