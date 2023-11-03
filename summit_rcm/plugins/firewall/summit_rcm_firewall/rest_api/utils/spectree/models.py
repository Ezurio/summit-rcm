"""Module to hold SpecTree Models"""

from typing import List, Optional
from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy


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


class ForwardedPortsResponseModel(BaseModel):
    """Model for the response to a request for forwarded ports"""

    __root__: List[ForwardedPortModel]


class ForwardedPortsResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for forwarded ports (legacy)"""

    Forward: Optional[List[ForwardedPortModel]]
