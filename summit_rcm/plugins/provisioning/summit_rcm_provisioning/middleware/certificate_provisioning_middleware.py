"""
Module that handles certificate provisioning tasks
"""
import asyncio
from datetime import datetime, timezone
from syslog import LOG_ERR, syslog
from typing import Any, Optional
import falcon.asgi
from summit_rcm_provisioning.services.provisioning_service import (
    ProvisioningState,
    CertificateProvisioningService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS, SUMMIT_RCM_TIME_FORMAT

UNPROVISIONED_PATH_WHITE_LIST = [
    # legacy routes
    "/datetime",
    "/certificateProvisioning",
    "/networkStatus",
    "/version",
    "/poweroff",
    "/reboot",
    # v2 routes
    "/api/v2/system/datetime",
    "/api/v2/system/certificateProvisioning",
    "/api/v2/network/status",
    "/api/v2/system/version",
    "/api/v2/system/power",
]


class CertificateProvisioningMiddleware:
    """Middleware that handles certificate provisioning tasks"""

    def __init__(
        self,
        provisioning_state: ProvisioningState = ProvisioningState.FULLY_PROVISIONED,
    ):
        self._provisioning_state: ProvisioningState = provisioning_state
        self._last_cert_hash: int = None

    async def check_for_time_set_request(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ):
        """
        Check for a request to set the date/time. If found, validate the timestamp before allowing
        the request to proceed.
        """
        try:
            if req.method != "PUT":
                return

            if req.path == "/datetime":
                post_data = await req.get_media()
                zone = post_data.get("zone", "")
                method = post_data.get("method", "")
                dt = post_data.get("datetime", "")

                if not zone and method == "manual" and dt:
                    # User is attempting to set the date/time manually via legacy route
                    if not CertificateProvisioningService.validate_new_timestamp(
                        int(dt), req
                    ):
                        result = {
                            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                            "InfoMsg": "Invalid timestamp",
                        }

                        # Return current timestamp and validity period
                        result["time"] = (
                            datetime.now(timezone.utc)
                            .astimezone()
                            .strftime(SUMMIT_RCM_TIME_FORMAT)
                        )
                        try:
                            (
                                not_before,
                                not_after,
                            ) = CertificateProvisioningService.get_validity_period(req)
                            result["notBefore"] = not_before.strftime(
                                SUMMIT_RCM_TIME_FORMAT
                            )
                            result["notAfter"] = not_after.strftime(
                                SUMMIT_RCM_TIME_FORMAT
                            )
                        except Exception as exception:
                            syslog(
                                LOG_ERR,
                                f"Could not retrieve validity period - {str(exception)}",
                            )

                        resp.status = falcon.HTTP_200
                        resp.media = result
                        resp.complete = True
            elif req.path == "/api/v2/system/datetime":
                post_data = await req.get_media()
                zone = post_data.get("zone", "")
                dt = post_data.get("datetime", "")

                if not zone and dt:
                    # User is attempting to set the date/time manually via v2 route
                    if not CertificateProvisioningService.validate_new_timestamp(
                        int(dt), req
                    ):
                        resp.status = falcon.HTTP_400
                        result = {}
                        # Return current timestamp and validity period
                        result["time"] = (
                            datetime.now(timezone.utc)
                            .astimezone()
                            .strftime(SUMMIT_RCM_TIME_FORMAT)
                        )
                        try:
                            (
                                not_before,
                                not_after,
                            ) = CertificateProvisioningService.get_validity_period(req)
                            result["notBefore"] = not_before.strftime(
                                SUMMIT_RCM_TIME_FORMAT
                            )
                            result["notAfter"] = not_after.strftime(
                                SUMMIT_RCM_TIME_FORMAT
                            )
                        except Exception as exception:
                            syslog(
                                LOG_ERR,
                                f"Could not retrieve validity period - {str(exception)}",
                            )
                            resp.status = falcon.HTTP_500

                        resp.media = result
                        resp.complete = True
        except Exception:
            pass

    async def check_for_time_set_response(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ):
        """
        Check for a response to set the date/time. If found, check if we need to update the
        provisioning state.
        """
        try:
            if req.method != "PUT":
                return

            if not (
                req.path == "/datetime"
                and resp.media.get("SDCERR", SUMMIT_RCM_ERRORS["SDCERR_FAIL"])
                == SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            ) and not (
                req.path == "/api/v2/system/datetime" and resp.status == falcon.HTTP_200
            ):
                return

            if (
                CertificateProvisioningService.get_provisioning_state()
                != ProvisioningState.PARTIALLY_PROVISIONED
            ):
                return

            CertificateProvisioningService.set_provisioning_state(
                ProvisioningState.FULLY_PROVISIONED
            )

            # Trigger a restart of Summit RCM to ensure the new SSL configuration takes effect
            async def delay(coro, seconds):
                await asyncio.sleep(seconds)
                await coro()

            asyncio.create_task(
                delay(CertificateProvisioningService.restart_summit_rcm, 0.1)
            )
        except Exception:
            pass

    def check_for_new_fallback_timestamp(self, req: falcon.asgi.Request):
        """
        Check if the client certificate's validity period starts after the current fallback
        timestamp. If so, update the fallback timestamp.
        """
        if self._provisioning_state != ProvisioningState.FULLY_PROVISIONED:
            return

        try:
            cert_hash = CertificateProvisioningService.get_client_cert_hash(req)

            if self._last_cert_hash == cert_hash:
                return

            self._last_cert_hash = cert_hash
        except Exception:
            pass

        try:
            (
                client_cert_not_before,
                _,
            ) = CertificateProvisioningService.get_client_cert_validity_period(req)

            try:
                fallback_timestamp = (
                    CertificateProvisioningService.read_fallback_timestamp()
                )
            except Exception:
                fallback_timestamp = None

            if not fallback_timestamp or client_cert_not_before > fallback_timestamp:
                # The client certificate's validity period starts after the fallback timestamp, so
                # update it
                syslog(
                    "Updating fallback timestamp to "
                    f"{str(int(client_cert_not_before.timestamp()))}"
                )
                CertificateProvisioningService.set_fallback_timestamp(
                    client_cert_not_before
                )
        except Exception as exception:
            # Couldn't read the validity period from the client certificate, so just continue
            syslog(
                f"Couldn't read validity period from client certificate - {str(exception)}"
            )

    async def process_request(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ):
        """Process an HTTP(S) request"""
        # Perform checks for special cases
        self.check_for_new_fallback_timestamp(req)
        await self.check_for_time_set_request(req, resp)

        # If we're fully provisioned, we don't need to do any further checks
        if self._provisioning_state == ProvisioningState.FULLY_PROVISIONED:
            return

        # If we're partially or unprovisioned, we only allow requests to the following paths:
        if req.path not in UNPROVISIONED_PATH_WHITE_LIST:
            resp.status = falcon.HTTP_401
            resp.complete = True

    async def process_response(
        self,
        req: falcon.asgi.Request,
        resp: falcon.asgi.Response,
        _: Optional[Any],
        req_succeeded: bool,
    ):
        """Process an HTTP(S) response"""
        if req_succeeded:
            await self.check_for_time_set_response(req, resp)
