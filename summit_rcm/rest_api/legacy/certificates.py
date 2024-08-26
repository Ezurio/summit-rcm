#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Module to handle legacy certificates endpoint"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.services.files_service import FilesService
from summit_rcm import definition
from summit_rcm.services.certificates_service import CertificatesService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        UnauthorizedErrorResponseModel,
        CertificateInfoResponseLegacy,
        CertificateInfoRequestQueryLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    UnauthorizedErrorResponseModel = None
    CertificateInfoResponseLegacy = None
    CertificateInfoRequestQueryLegacy = None
    network_tag = None


spec = SpectreeService()


class Certificates:
    """
    Certificate management
    """

    @spec.validate(
        query=CertificateInfoRequestQueryLegacy,
        resp=Response(
            HTTP_200=CertificateInfoResponseLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, req, resp):
        """
        Retrieve either a list of all certificates or info on just one if the name parameter is
        provided (legacy)
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        cert_name = req.params.get("name", None)
        password = req.params.get("password", None)
        try:
            if cert_name:
                cert_info, info_msg = CertificatesService.get_cert_info(
                    cert_name, password
                )
                result["cert_info"] = cert_info
                result["InfoMsg"] = info_msg
                if len(cert_info) > 0:
                    result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                # No cert name give, so just return the list of certs available
                files = FilesService.get_cert_files()
                result["files"] = files
                result["count"] = len(files)
                result["InfoMsg"] = "cert files"
                result["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as exception:
            syslog(LOG_ERR, f"Could not read certificate info: {str(exception)}")
            result["InfoMsg"] = "Could not read certificate info"

        resp.media = result
