"""Module to hold SpecTree Models"""

from pydantic import BaseModel
from summit_rcm.rest_api.utils.spectree.models import DefaultResponseModelLegacy
from summit_rcm.systemd_unit import SystemdActiveStateEnum


class StunnelStateModel(BaseModel):
    """Model for reading/configuration the stunnel state"""

    state: SystemdActiveStateEnum


class StunnelStateModelLegacy(DefaultResponseModelLegacy):
    """Model for a request to set the stunnel state (legacy)"""

    state: SystemdActiveStateEnum
