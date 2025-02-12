#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""
Generate the OpenAPI spec for the Summit RCM REST API for the log forwarding plugin
"""


def generate_docs():
    """
    Generate the OpenAPI spec for the Summit RCM REST API for the log forwarding plugin. This
    function is called duriong the build process to generate the OpenAPI spec for the log forwarding
    plugin.
    """
    from summit_rcm.rest_api.utils.spectree.generate_api_spec import generate_api_spec

    routes = {}

    try:
        from summit_rcm_log_forwarding.rest_api.legacy.log_forwarding import (
            LogForwarding,
        )

        routes["/logForwarding"] = LogForwarding
    except ImportError:
        pass

    try:
        from summit_rcm_log_forwarding.rest_api.v2.system.log_forwarding import (
            LogForwardingResource,
        )

        routes["/api/v2/system/logs/forwarding"] = LogForwardingResource
    except ImportError:
        pass

    generate_api_spec(routes)


if __name__ == "__main__":
    generate_docs()
