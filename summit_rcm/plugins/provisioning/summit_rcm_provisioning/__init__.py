#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Init File to setup the Provisioning Plugin"""

from syslog import syslog, LOG_ERR
import ssl
from typing import Optional
from summit_rcm_provisioning.services.provisioning_service import (
    CertificateProvisioningService,
    ProvisioningState,
    provisioning_config,
)


async def get_legacy_supported_routes():
    """Optional Function to return supported legacy routes"""
    routes = []
    routes.append("/certificateProvisioning")
    return routes


async def get_legacy_routes():
    """Function to import and return Provisioning API Routes"""
    routes = {}
    try:
        from summit_rcm_provisioning.rest_api.legacy.provisioning import (
            CertificateProvisioningResourceLegacy,
        )

        routes["/certificateProvisioning"] = CertificateProvisioningResourceLegacy()
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR,
            f"Error Importing certificate provisioning legacy routes: {str(exception)}",
        )
    return routes


async def get_v2_supported_routes():
    """Optional Function to return supported v2 routes"""
    routes = []
    routes.append("/api/v2/system/certificateProvisioning")
    return routes


async def get_v2_routes():
    """Function to import and return Provisioning API Routes"""
    routes = {}
    try:
        from summit_rcm_provisioning.rest_api.v2.system.provisioning import (
            CertificateProvisioningResource,
        )

        routes["/api/v2/system/certificateProvisioning"] = (
            CertificateProvisioningResource()
        )
    except ImportError:
        pass
    except Exception as exception:
        syslog(
            LOG_ERR,
            f"Error Importing certificate provisioning v2 routes: {str(exception)}",
        )
    return routes


async def get_middleware() -> Optional[list]:
    """Handler called when adding Falcon middleware"""
    from summit_rcm_provisioning.middleware.certificate_provisioning_middleware import (
        CertificateProvisioningMiddleware,
    )

    return [
        CertificateProvisioningMiddleware(
            CertificateProvisioningService().get_provisioning_state()
        )
    ]


async def server_config_preload_hook(config) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""
    provisioning_state = CertificateProvisioningService().get_provisioning_state()

    if provisioning_state == ProvisioningState.UNPROVISIONED:
        config.ssl_keyfile = provisioning_config.ssl_private_key
        config.ssl_certfile = provisioning_config.ssl_certificate
        config.ssl_ca_certs = ""
        syslog("*** RESTRICTED PROVISIONING MODE ***")
        return

    if provisioning_state == ProvisioningState.PARTIALLY_PROVISIONED:
        config.ssl_keyfile = provisioning_config.server_ssl_private_key
        config.ssl_certfile = provisioning_config.server_ssl_certificate
        config.ssl_ca_certs = provisioning_config.get(
            "global", "server.ssl_certificate_chain", ""
        )
        syslog("*** PARTIALLY PROVISIONED MODE ***")


async def server_config_postload_hook(config) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
    if (
        CertificateProvisioningService().get_provisioning_state()
        != ProvisioningState.FULLY_PROVISIONED
    ):
        # Don't require client certificates when not fully provisioned
        config.ssl.verify_mode = ssl.CERT_NONE
