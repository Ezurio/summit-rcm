"""Module to hold SpecTree Models"""

from typing import List
try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy


class ChronySourceModel(BaseModel):
    """Model for a chrony NTP source"""

    address: str
    type: str


class ChronySourcesResponseModel(BaseModel):
    """Model for the response to a request for chrony NTP sources"""

    __root__: List[ChronySourceModel]


class ChronySourcesRequestModelLegacy(BaseModel):
    """Model for chrony NTP sources (legacy)"""

    sources: List[ChronySourceModel]


class ChronySourcesResponseModelLegacy(
    DefaultResponseModelLegacy, ChronySourcesRequestModelLegacy
):
    """Model for the response to a request for chrony NTP sources (legacy)"""
