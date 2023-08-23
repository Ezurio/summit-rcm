"""
Module to interact with certificates
"""

from syslog import LOG_ERR, syslog
import falcon.asgi.multipart
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)
from summit_rcm.services.certificates_service import CertificatesService


class CertificatesResource:
    """
    Resource to handle queries and requests for certificates
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/certificates endpoint
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

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ) -> None:
        """
        GET handler for the /network/certificates/{name} endpoint
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

    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ):
        """
        POST handler for the /network/certificates/{name} endpoint
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

    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, name: str
    ):
        """
        DELETE handler for the /network/certificates/{name} endpoint
        """
        try:
            FilesService.delete_cert_file(name)
            resp.status = falcon.HTTP_200
        except FileNotFoundError:
            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(f"Could not delete certificate - {str(exception)}")
            resp.status = falcon.HTTP_500
