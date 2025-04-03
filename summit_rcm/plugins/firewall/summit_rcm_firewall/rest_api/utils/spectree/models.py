#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from typing import List, Optional
from summit_rcm.rest_api.utils.spectree.models import (
    DefaultResponseModelLegacy,
    BaseModel,
    RootModel,
)


class ForwardedPortModel(BaseModel):
    """Model for a forwarded port"""

    port: int
    protocol: str
    toport: str
    toaddr: str
    ipVersion: str


class ForwardedPortModelLegacy(BaseModel):
    """Model for a forwarded port"""

    port: int
    protocol: str
    toport: str
    toaddr: str
    ip_version: str


class ForwardedPortsResponseModel(RootModel):
    """Model for the response to a request for forwarded ports"""

    root: List[ForwardedPortModel]


class ForwardedPortsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for forwarded ports (legacy)"""

    Forward: Optional[List[ForwardedPortModel]] = None
