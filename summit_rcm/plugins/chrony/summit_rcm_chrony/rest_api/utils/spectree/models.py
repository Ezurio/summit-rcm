#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from typing import List
from summit_rcm.rest_api.utils.spectree.models import (
    DefaultResponseModelLegacy,
    BaseModel,
    RootModel,
)


class ChronySourceModel(BaseModel):
    """Model for a chrony NTP source"""

    address: str
    type: str


class ChronySourcesResponseModel(RootModel):
    """Model for the response to a request for chrony NTP sources"""

    root: List[ChronySourceModel]


class ChronySourcesRequestModelLegacy(BaseModel):
    """Model for chrony NTP sources (legacy)"""

    sources: List[ChronySourceModel]


class ChronySourcesResponseModelLegacy(
    DefaultResponseModelLegacy, ChronySourcesRequestModelLegacy
):
    """Model for the response to a request for chrony NTP sources (legacy)"""
