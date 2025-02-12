#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the unauthenticated plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the unauthenticated plugin. This
    function is called duriong the build process to generate the OpenAPI spec for the
    unauthenticated plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_unauthenticated.rest_api.legacy.unauthenticated import (
            AllowUnauthenticatedResourceLegacy,
        )

        routes["/allowUnauthenticatedResetReboot"] = AllowUnauthenticatedResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_unauthenticated.rest_api.v2.system.unauthenticated import (
            AllowUnauthenticatedResource,
        )

        routes["/api/v2/system/allowUnauthenticatedResetReboot"] = (
            AllowUnauthenticatedResource
        )
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
