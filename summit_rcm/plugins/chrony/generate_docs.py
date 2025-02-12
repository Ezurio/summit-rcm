#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the Chrony plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the Chrony plugin. This function is
    called duriong the build process to generate the OpenAPI spec for the Chrony plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_chrony.rest_api.legacy.ntp import NTPResourceLegacy

        routes["/ntp"] = NTPResourceLegacy
        routes["/ntp/{command}"] = NTPResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_chrony.rest_api.v2.system.ntp import (
            NTPSourcesResource,
            NTPSourceResource,
        )

        routes["/api/v2/system/datetime/ntp"] = NTPSourcesResource
        routes["/api/v2/system/datetime/ntp/{address}"] = NTPSourceResource
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
