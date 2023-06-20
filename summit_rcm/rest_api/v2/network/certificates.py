"""
Module to interact with certificates
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.rest_api.legacy.files import FilesManage
from summit_rcm.services.certificates_service import CertificatesService


class CertificatesResource:
    """
    Resource to handle queries and requests for certificates
    """

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /network/certificates endpoint
        """
        try:
            cert_name = req.params.get("name", None)
            try:
                post_data = await req.get_media()
                password = post_data.get("password", None)
            except falcon.MediaNotFoundError:
                password = None

            if cert_name:
                cert_info, info_msg = CertificatesService.get_cert_info(
                    cert_name, password
                )

                if len(cert_info) <= 0:
                    syslog(f"Could not read certificate info: {str(info_msg)}")
                    resp.status = falcon.HTTP_500
                    return

                resp.media = cert_info
                resp.status = falcon.HTTP_200
                resp.content_type = falcon.MEDIA_JSON
                return

            # No cert name give, so just return the list of certs available
            resp.media = FilesManage.get_cert_or_pac_files("cert")
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(
                LOG_ERR, f"Unable to retrieve certificate information: {str(exception)}"
            )
            resp.status = falcon.HTTP_500
