#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the AWM plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the AWM plugin. This function is
    called duriong the build process to generate the OpenAPI spec for the AWM plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_awm.rest_api.legacy.awm import AWMResourceLegacy

        routes["/awm"] = AWMResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_awm.rest_api.v2.network.awm import AWMResource

        routes["/api/v2/network/wifi/awm"] = AWMResource
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
