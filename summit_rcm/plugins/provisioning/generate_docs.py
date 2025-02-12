#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the certificate provisioning plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the certificate provisioning plugin.
    This function is called duriong the build process to generate the OpenAPI spec for the
    certificate provisioning plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_provisioning.rest_api.legacy.provisioning import (
            CertificateProvisioningResourceLegacy,
        )

        routes["/certificateProvisioning"] = CertificateProvisioningResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_provisioning.rest_api.v2.system.provisioning import (
            CertificateProvisioningResource,
        )

        routes["/api/v2/system/certificateProvisioning"] = (
            CertificateProvisioningResource
        )
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
