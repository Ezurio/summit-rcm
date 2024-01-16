"""
Module to interact with legacy certificate provisioning
"""
import asyncio
from syslog import syslog, LOG_ERR
from pathlib import Path
import falcon.asgi
from summit_rcm_provisioning.services.provisioning_service import (
    CertificateProvisioningService,
    InvalidCertificateError,
    ProvisioningState,
    DEVICE_SERVER_CSR_PATH,
    CONFIG_FILE_TEMP_PATH,
)
from summit_rcm.rest_api.services.rest_files_service import (
    RESTFilesService as FilesService,
)
from summit_rcm.definition import CERT_TEMP_PATH, SUMMIT_RCM_ERRORS


class CertificateProvisioningResourceLegacy:
    """
    Resource to handle queries and requests for legacy certificate provisioning
    """

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /certificateProvisioning endpoint
        """
        resp.media = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
            "state": CertificateProvisioningService().get_provisioning_state(),
        }
        resp.content_type = falcon.MEDIA_JSON
        resp.status = falcon.HTTP_200

    async def on_post(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        POST handler for the /certificateProvisioning endpoint
        """
        try:
            if (
                CertificateProvisioningService().get_provisioning_state()
                != ProvisioningState.UNPROVISIONED
            ):
                raise ValueError

            form = await req.get_media()
            if not isinstance(form, falcon.asgi.multipart.MultipartForm):
                raise ValueError

            openssl_key_gen_args = ""
            config_file_found = False

            async for part in form:
                if part.name == "configFile":
                    config_file_found = True

                    if not part.filename.endswith(".cnf"):
                        raise ValueError

                    if not await FilesService.handle_file_upload_multipart_form_part(
                        part, CONFIG_FILE_TEMP_PATH
                    ):
                        raise Exception("error uploading file")
                elif part.name == "opensslKeyGenArgs":
                    openssl_key_gen_args = str(await part.text)

            if not config_file_found:
                raise ValueError

            await CertificateProvisioningService.generate_key_and_csr(
                openssl_key_gen_args=openssl_key_gen_args
            )

            resp.stream = await FilesService().handle_file_download(
                DEVICE_SERVER_CSR_PATH
            )
            resp.content_type = "application/x-download"
            resp.status = falcon.HTTP_200
        except ValueError:
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(LOG_ERR, f"Couldn't generate key and CSR: {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            # Remove the temporary config file, if present
            Path(CONFIG_FILE_TEMP_PATH).unlink(missing_ok=True)

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /certificateProvisioning endpoint
        """
        try:
            result = {"SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"], "InfoMsg": ""}
            resp.status = falcon.HTTP_200

            if (
                CertificateProvisioningService().get_provisioning_state()
                != ProvisioningState.UNPROVISIONED
            ):
                result["InfoMsg"] = "Already provisioned"
                resp.media = result
                return

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
                        part, CERT_TEMP_PATH
                    ):
                        raise Exception("error uploading file")

            if not cert_file_found:
                result["InfoMsg"] = "No filename specified"
                resp.media = result
                return

            await CertificateProvisioningService.save_certificate_file()

            # Trigger a restart of Summit RCM to ensure the new SSL configuration takes effect
            async def delay(coro, seconds):
                await asyncio.sleep(seconds)
                await coro()

            asyncio.create_task(
                delay(CertificateProvisioningService.restart_summit_rcm, 0.1)
            )

            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except (InvalidCertificateError, ValueError):
            result["InfoMsg"] = "Invalid certificate file"
        except Exception as exception:
            syslog(LOG_ERR, f"Couldn't upload certificate file: {str(exception)}")
            result["InfoMsg"] = "Error uploading certificate file"
        resp.media = result
