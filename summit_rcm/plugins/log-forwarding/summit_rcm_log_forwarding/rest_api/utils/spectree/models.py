#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from typing import Optional
try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy
from summit_rcm.systemd_unit import SystemdActiveStateEnum


class LogForwardingStateModel(BaseModel):
    """Model for reading/configuration the log forwarding state"""

    state: SystemdActiveStateEnum


class LogForwardingStateModelLegacy(DefaultResponseModelLegacy):
    """Model for a request to set the log forwarding state (legacy)"""

    state: SystemdActiveStateEnum


class LogForwardingSetStateResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for a request to set the log forwarding state (legacy)"""

    log_forwarding_state: Optional[SystemdActiveStateEnum]
