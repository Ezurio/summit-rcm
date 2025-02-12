#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the firewall plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the firewall plugin. This function is
    called duriong the build process to generate the OpenAPI spec for the firewall plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_firewall.rest_api.legacy.firewall import (
            FirewallResourceLegacy,
        )

        routes["/firewall"] = FirewallResourceLegacy
        routes["/firewall/{command}"] = FirewallResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_firewall.rest_api.v2.network.firewall import (
            FirewallForwardedPortsResource,
        )

        routes["/api/v2/network/firewall/forwardedPorts"] = (
            FirewallForwardedPortsResource
        )
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
