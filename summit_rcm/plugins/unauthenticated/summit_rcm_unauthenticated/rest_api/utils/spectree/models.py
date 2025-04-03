#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from summit_rcm.rest_api.utils.spectree.models import (
    DefaultResponseModelLegacy,
    BaseModel,
)


class AllowUnauthenticatedRebootResetStateModel(BaseModel):
    """Model for the response to a request for the allowUnauthenticatedRebootReset state"""

    allowUnauthenticatedRebootReset: bool


class AllowUnauthenticatedRebootResetStateModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for the allowUnauthenticatedRebootReset state (legacy)"""

    allowUnauthenticatedRebootReset: bool
