#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the radio SISO mode plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the radio SISO mode plugin. This
    function is called duriong the build process to generate the OpenAPI spec for the radio SISO
    mode plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_radio_siso_mode.rest_api.legacy.radio_siso_mode import (
            RadioSISOModeResourceLegacy,
        )

        routes["/radioSISOMode"] = RadioSISOModeResourceLegacy
    except ImportError:
        pass

    try:
        from summit_rcm_radio_siso_mode.rest_api.v2.network.radio_siso_mode import (
            RadioSISOModeResource,
        )

        routes["/api/v2/network/wifi/radioSISOMode"] = RadioSISOModeResource
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
