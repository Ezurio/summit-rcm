#!/usr/bin/env python3

"""Generate the OpenAPI spec for the Summit RCM REST API"""

import json
import os
import falcon.asgi
from typing import Any, Dict, Optional

# Set the environment variable to indicate that we are generating the docs
os.environ["DOCS_GENERATION"] = "True"

from summit_rcm.rest_api.services.spectree_service import SpectreeService


def generate_api_spec(routes: Optional[Dict[str, Any]] = None) -> None:
    """Generate the OpenAPI spec for the REST API"""

    # Create a falcon ASGI app, load the provided routes, and register the app with the Spectree
    # service
    app = falcon.asgi.App()
    if routes:
        for route, resource in routes.items():
            app.add_route(route, resource())
    SpectreeService().register(app)

    # Generate the spec JSON and save it to a file
    openapi_json_file_path = os.environ.get(
        "OPENAPI_JSON_PATH", "summit-rcm-openapi.json"
    )
    with open(openapi_json_file_path, "w") as openapi_json_file:
        json.dump(SpectreeService().spec.spec, openapi_json_file)

    print(f"Summit RCM OpenAPI spec generated: {openapi_json_file_path}")
