#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2026 Ezurio LLC.
#
"""
Module that handles unauthenticated access tasks
"""

from typing import Any, Optional
import falcon.asgi
from summit_rcm import SessionCheckingMiddleware
from summit_rcm_unauthenticated.services.unauthenticated_service import (
    UnauthenticatedService,
)

UNAUTHENTICATED_PATH_LIST = [
    # legacy routes
    "factoryReset",
    "reboot",
    "/factoryReset",
    "/reboot",
    # v2 routes
    "/api/v2/system/power",
    "/api/v2/system/factoryReset",
]


class UnauthenticatedMiddleware:
    """Middleware that handles unauthenticated access tasks"""

    async def process_request(
        self, req: falcon.asgi.Request, _resp: falcon.asgi.Response
    ):
        """Process an HTTP(S) request"""
        if req.path in UNAUTHENTICATED_PATH_LIST:
            if UnauthenticatedService().get_allow_unauthenticated_enabled():
                for path in UNAUTHENTICATED_PATH_LIST:
                    if path in SessionCheckingMiddleware().paths:
                        SessionCheckingMiddleware().paths.remove(path)
            else:
                for path in UNAUTHENTICATED_PATH_LIST:
                    if path not in SessionCheckingMiddleware().paths:
                        SessionCheckingMiddleware().paths.append(path)

    async def process_response(
        self,
        _req: falcon.asgi.Request,
        _resp: falcon.asgi.Response,
        _: Optional[Any],
        req_succeeded: bool,
    ):
        """Process an HTTP(S) response"""
