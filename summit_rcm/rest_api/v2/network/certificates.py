"""
Module to interact with certificates
"""

from syslog import LOG_ERR, syslog
import falcon.asgi.multipart
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)
from summit_rcm.services.certificates_service import CertificatesService

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        CertificateFiles,
        CertificateInfoRequest,
        CertificateInfoResponse,
        CertificateUploadRequestFormModel,
        InternalServerErrorResponseModel,
        NotFoundErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    CertificateFiles = None
    CertificateInfoRequest = None
    CertificateInfoResponse = None
    CertificateUploadRequestFormModel = None
    InternalServerErrorResponseModel = None
    NotFoundErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    network_tag = None


spec = SpectreeService()


class CertificatesResource:
    """
    Resource to handle queries and requests for certificates
    """

    @spec.validate(
        resp=Response(
            HTTP_200=CertificateFiles,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of uploaded certificates/.pac files
        """
        try:
            resp.media = FilesService.get_cert_and_pac_files()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR, f"Unable to retrieve certificate information: {str(exception)}"
            )
            resp.status = falcon.HTTP_500


class CertificateResource:
    """Resource to handle queries and requests for a specific certificate by name"""

    @spec.validate(
        json=CertificateInfoRequest,
        resp=Response(
            HTTP_200=CertificateInfoResponse,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """
        Retrieve info about a specific certificate
        """
        try:
            try:
                post_data = await req.get_media()
                password = post_data.get("password", None)
            except falcon.MediaNotFoundError:
                password = None

            cert_info, info_msg = CertificatesService.get_cert_info(name, password)

            if len(cert_info) <= 0:
                syslog(f"Could not read certificate info: {str(info_msg)}")
                resp.status = falcon.HTTP_500
                return

            resp.media = cert_info
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR, f"Unable to retrieve certificate information: {str(exception)}"
            )
            resp.status = falcon.HTTP_500

    @spec.validate(
        form=CertificateUploadRequestFormModel,
        resp=Response(
            HTTP_201=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ):
        """
        Upload a new certificate
        """
        try:
            form: falcon.asgi.multipart.MultipartForm = await req.get_media()
            if not isinstance(form, falcon.asgi.multipart.MultipartForm):
                raise Exception()
        except Exception:
            resp.status = falcon.HTTP_400
            return

        async for part in form:
            if part.name == "file":
                try:
                    if not await FilesService.handle_cert_file_upload_multipart_form(
                        part, name
                    ):
                        raise Exception("Error saving file to disk")

                    resp.status = falcon.HTTP_201
                    return
                except Exception as exception:
                    syslog(f"Could not upload file - {str(exception)}")
                    resp.status = falcon.HTTP_500
                    return

        # The form is missing a 'file' part
        resp.status = falcon.HTTP_400

    @spec.validate(
        resp=Response(
            HTTP_200=None,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_404=NotFoundErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ):
        """
        Remove a specific certificate
        """
        try:
            FilesService.delete_cert_file(name)
            resp.status = falcon.HTTP_200
        except FileNotFoundError:
            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(f"Could not delete certificate - {str(exception)}")
            resp.status = falcon.HTTP_500
