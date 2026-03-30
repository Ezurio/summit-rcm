#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""Init File to setup the Provisioning Plugin"""

from syslog import syslog, LOG_ERR, LOG_INFO
import ssl
from pathlib import Path
from typing import Optional
from summit_rcm_provisioning.services.provisioning_service import (
    CertificateProvisioningService,
    ProvisioningState,
)
from summit_rcm.settings import ServerConfig


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


def _rebuild_trust_store(parser) -> None:
    """Rebuild the TLS trust store from the rodata CA and paired client cert.

    Concatenates the immutable rodata CA cert with the paired client cert
    (if present) and writes the result to the ssl_certificate_chain path.
    This only writes the file to disk; callers set config.ssl_ca_certs as needed.
    """
    rodata_ca = parser["summit-rcm"].get("rodata_ca_cert_path", "").strip('"')
    paired_cert = parser["summit-rcm"].get("paired_client_cert_path", "").strip('"')
    ca_crt_path = (
        parser["global"].get("server.ssl_certificate_chain", "").strip('"')
    )

    if not rodata_ca or not ca_crt_path:
        return

    rodata_ca_path = Path(rodata_ca)
    if not rodata_ca_path.exists():
        syslog(LOG_ERR, f"rodata CA cert not found: {rodata_ca}")
        return

    trust_store = rodata_ca_path.read_bytes()
    if paired_cert:
        paired_cert_path = Path(paired_cert)
        if paired_cert_path.exists():
            trust_store += b"\n" + paired_cert_path.read_bytes()

    ca_crt = Path(ca_crt_path)
    ca_crt.parent.mkdir(parents=True, exist_ok=True)
    ca_crt.write_bytes(trust_store)
    syslog(LOG_INFO, f"Trust store rebuilt at {ca_crt_path}")


async def server_config_preload_hook(config) -> None:
    """Hook function called before the Uvicorn ASGI server config is loaded"""
    provisioning_state = CertificateProvisioningService().get_provisioning_state()

    if provisioning_state == ProvisioningState.UNPROVISIONED:
        config.ssl_keyfile = "/etc/summit-rcm/ssl/provisioning.key"
        config.ssl_certfile = "/etc/summit-rcm/ssl/provisioning.crt"
        config.ssl_ca_certs = ""

        # Ensure the trust store exists for UNPROVISIONED when client pairing
        # is enabled (the trust store file may not exist yet on first boot)
        parser = ServerConfig().get_parser()
        enable_client_pairing = parser["summit-rcm"].getboolean(
            "enable_client_pairing", fallback=False
        )
        if enable_client_pairing:
            _rebuild_trust_store(parser)

        syslog("*** RESTRICTED PROVISIONING MODE ***")
        return

    if provisioning_state == ProvisioningState.PARTIALLY_PROVISIONED:
        parser = ServerConfig().get_parser()
        config.ssl_keyfile = (
            parser["global"]
            .get("server.ssl_private_key", "/etc/summit-rcm/ssl/server.key")
            .strip('"')
        )
        config.ssl_certfile = (
            parser["global"]
            .get("server.ssl_certificate", "/etc/summit-rcm/ssl/server.crt")
            .strip('"')
        )
        config.ssl_ca_certs = (
            parser["global"]
            .get(
                "server.ssl_certificate_chain",
                "",
            )
            .strip('"')
        )

        enable_client_pairing = parser["summit-rcm"].getboolean(
            "enable_client_pairing", fallback=False
        )
        if enable_client_pairing:
            _rebuild_trust_store(parser)

        syslog("*** PARTIALLY PROVISIONED MODE ***")


async def server_config_postload_hook(config) -> None:
    """Hook function called after the Uvicorn ASGI server config is loaded"""
    provisioning_state = CertificateProvisioningService().get_provisioning_state()
    enable_client_pairing = (
        ServerConfig()
        .get_parser()["summit-rcm"]
        .getboolean("enable_client_pairing", fallback=False)
    )

    if enable_client_pairing:
        # With client pairing enabled, only UNPROVISIONED gets CERT_NONE.
        # PARTIALLY uses CERT_REQUIRED against the CA trust store.
        if provisioning_state == ProvisioningState.UNPROVISIONED:
            config.ssl.verify_mode = ssl.CERT_NONE
    else:
        # Default behavior: don't require client certificates when not fully
        # provisioned (both UNPROVISIONED and PARTIALLY get CERT_NONE)
        if provisioning_state != ProvisioningState.FULLY_PROVISIONED:
            config.ssl.verify_mode = ssl.CERT_NONE
