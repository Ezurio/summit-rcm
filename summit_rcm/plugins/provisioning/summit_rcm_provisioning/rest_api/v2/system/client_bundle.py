#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2026 Ezurio LLC.
#
"""
Module to interact with client certificate pairing
"""

import asyncio
from pathlib import Path
from syslog import syslog, LOG_ERR
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_provisioning.services.provisioning_service import (
    CertificateProvisioningService,
    ProvisioningState,
)
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_provisioning.rest_api.utils.spectree.models import (
        CertificateProvisioningClientBundleUploadRequestFormModel,
    )
    from summit_rcm_provisioning.rest_api.utils.spectree.tags import (
        certificate_provisioning_tag,
    )
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    CertificateProvisioningClientBundleUploadRequestFormModel = None
    certificate_provisioning_tag = None


spec = SpectreeService()

PAIRED_CLIENT_CERT_TEMP_PATH = "/tmp/paired_client.crt"


class CertificateProvisioningClientBundleResource:
    """
    Resource to handle client certificate pairing
    """

    @spec.validate(
        form=CertificateProvisioningClientBundleUploadRequestFormModel,
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[certificate_provisioning_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Upload a client certificate for device pairing

        This endpoint accepts a PEM-encoded client certificate and saves it as the
        paired client certificate. The TLS trust store is rebuilt to include the new
        certificate, and Summit RCM restarts to apply the updated configuration.

        Only available in the PARTIALLY_PROVISIONED state.
        """
        try:
            if (
                CertificateProvisioningService().get_provisioning_state()
                != ProvisioningState.PARTIALLY_PROVISIONED
            ):
                raise ValueError

            form = await req.get_media()
            if not isinstance(form, falcon.asgi.multipart.MultipartForm):
                raise ValueError

            cert_file_found = False

            async for part in form:
                if part.name == "certificate":
                    cert_file_found = True

                    if not part.filename.endswith(
                        ".crt"
                    ) and not part.filename.endswith(".pem"):
                        raise ValueError

                    if not await FilesService.handle_file_upload_multipart_form_part(
                        part, PAIRED_CLIENT_CERT_TEMP_PATH
                    ):
                        raise Exception("error uploading file")

            if not cert_file_found:
                raise ValueError

            await CertificateProvisioningService.save_paired_client_cert(
                PAIRED_CLIENT_CERT_TEMP_PATH
            )

            # Trigger a restart of Summit RCM to rebuild the trust store
            async def delay(coro, seconds):
                await asyncio.sleep(seconds)
                await coro()

            asyncio.create_task(
                delay(CertificateProvisioningService.restart_summit_rcm, 0.1)
            )

            resp.status = falcon.HTTP_200
        except ValueError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(
                LOG_ERR, f"Couldn't upload paired client certificate: {str(exception)}"
            )
            resp.status = falcon.HTTP_500
        finally:
            Path(PAIRED_CLIENT_CERT_TEMP_PATH).unlink(missing_ok=True)
