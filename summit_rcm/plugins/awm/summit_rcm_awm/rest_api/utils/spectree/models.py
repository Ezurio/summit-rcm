"""Module to hold SpecTree Models"""

from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy


class AWMStateResponseModel(BaseModel):
    """Model for the response to a request for AWM state"""

    geolocationScanningEnabled: int


class AWMStateRequestModelLegacy(BaseModel):
    """Model for a request to set the AWM state (legacy)"""

    geolocation_scanning_enable: int


class AWMStateResponseModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for AWM state (legacy)"""

    geolocation_scanning_enable: int
