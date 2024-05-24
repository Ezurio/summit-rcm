"""Module to hold SpecTree Models"""

try:
    from pydantic.v1 import BaseModel
except ImportError:
    from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy
from summit_rcm_radio_siso_mode.services.radio_siso_mode_service import (
    RadioSISOModeEnum,
)


class SISOModeStateModel(BaseModel):
    """Model for the response to a request for SISO mode"""

    sisoMode: RadioSISOModeEnum


class SISOModeStateModelLegacy(BaseModel):
    """Model for the response to a request for SISO mode"""

    SISO_mode: RadioSISOModeEnum


class SISOModeStateResponseModelLegacy(
    DefaultResponseModelLegacy, SISOModeStateModelLegacy
):
    """Model for the response to a request for SISO mode (legacy)"""
