#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to hold SpecTree Models"""

from typing import Optional
from spectree import BaseFile
from summit_rcm_provisioning.services.provisioning_service import (
    ProvisioningState,
)
from summit_rcm.rest_api.utils.spectree.models import (
    DefaultResponseModelLegacy,
    BaseModel,
)


class CertificateProvisioningStateModel(BaseModel):
    """Model for the response to a request for certificate provisioning state"""

    state: ProvisioningState


class CertificateProvisioningStateModelLegacy(DefaultResponseModelLegacy):
    """Model for the response to a request for certificate provisioning state (legacy)"""

    state: ProvisioningState


class CertificateProvisioningCsrGenerationRequestFormModel(BaseModel):
    """Model for a request to generate a CSR"""

    configFile: BaseFile
    opensslKeyGenArgs: Optional[str] = None


class CertificateProvisioningCertUploadRequestFormModel(BaseModel):
    """Model for a request to upload a certificate"""

    certificate: BaseFile


class CertificateProvisioningClientBundleUploadRequestFormModel(BaseModel):
    """Model for a request to upload a paired client certificate"""

    certificate: BaseFile
