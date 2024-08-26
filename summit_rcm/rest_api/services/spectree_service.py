#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle SpecTree
"""

from syslog import syslog
from pathlib import Path
import json
import falcon.asgi

try:
    from spectree import SpecTree
    from summit_rcm.rest_api.utils.spectree.falcon_asgi_plugin import (
        SummitRcmFalconAsgiPlugin,
        OpenAPIAsgi,
        DocPageAsgi,
    )
except ImportError:
    SpecTree = None
from summit_rcm.settings import ServerConfig
from summit_rcm.utils import Singleton
from summit_rcm.definition import SUMMIT_RCM_VERSION

OPENAPI_JSON_PATH = "/etc/summit-rcm-openapi.json"
DOCS_PAGE_PATH = "api"
SWAGGER_PAGE_TEMPLATE = """
<!-- HTML for static distribution bundle build -->
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Summit RCM API Reference</title>
        <link rel="stylesheet" type="text/css"
        href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.3/swagger-ui.css" >
        <style>
        html
        {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}

        *,
        *:before,
        *:after
        {{
            box-sizing: inherit;
        }}

        body
        {{
            margin:0;
            background: #fafafa;
        }}
        </style>
    </head>

    <body>
        <div id="swagger-ui"></div>

        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.3/swagger-ui-bundle.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.11.3/swagger-ui-standalone-preset.js"></script>
        <script>
        window.onload = function() {{
        var full = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
        // Begin Swagger UI call region
        const ui = SwaggerUIBundle({{
            url: "{spec_url}",
            dom_id: '#swagger-ui',
            deepLinking: true,
            presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
            ],
            layout: "BaseLayout",
            withCredentials: true,
            persistAuthorization: true,
            requestSnippetsEnabled: true,
            validatorUrl: "none",
            tagsSorter: "alpha",
            tryItOutEnabled: true,
        }})
        ui.initOAuth({{
            clientId: "{client_id}",
            clientSecret: "{client_secret}",
            realm: "{realm}",
            appName: "{app_name}",
            scopeSeparator: "{scope_separator}",
            additionalQueryStringParams: {additional_query_string_params},
            useBasicAuthenticationWithAccessCodeGrant: {use_basic_authentication_with_access_code_grant},
            usePkceWithAuthorizationCodeGrant: {use_pkce_with_authorization_code_grant}
        }})
        // End Swagger UI call region

        window.ui = ui
        }}
    </script>
    </body>
</html>"""
SCALAR_PAGE_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Summit RCM API Reference</title>
    <meta charset="utf-8" />
    <meta
      name="viewport"
      content="width=device-width, initial-scale=1" />
    <style>
      body {{
        margin: 0;
      }}
    </style>
  </head>
  <body>
    <script
      id="api-reference"
      data-url="{spec_url}">
    </script>
    <script>
      var configuration = {{
        theme: 'default',
        isEditable: false,
        metaData: {{
            title: 'Summit RCM API Reference',
            description: 'Summit RCM API Reference',
        }},
      }}

      var apiReference = document.getElementById('api-reference')
      apiReference.dataset.configuration = JSON.stringify(configuration)
    </script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>"""


class RootDocumentationRedirectMiddleware:
    """
    Class for handling redirecting incoming requests to the root URL to the API documentation page.
    """

    async def process_request(
        self, req: falcon.asgi.Request, _: falcon.asgi.Response
    ) -> None:
        """
        Middleware function for handling redirecting incoming requests to the root URL to the API
        documentation page.
        """
        if req.path in ["", "/"]:
            req.path = SpectreeService().doc_page_path


class SpectreeService(metaclass=Singleton):
    """Service to handle Spectree"""

    def __init__(self) -> None:
        if SpecTree is None or Path(OPENAPI_JSON_PATH).exists():
            self.spec = None
            return

        self.spec = SpecTree(
            "falcon-asgi",
            title="Summit RCM API Reference",
            version=SUMMIT_RCM_VERSION,
            description="<p>This page provides an interactive reference and helpful code snippets "
            "for a variety of languages for the Summit RCM REST API.</p><p>If necessary, remember "
            " to first login to retrieve a valid session cookie before initiating a request to "
            "any restricted endpoints.</p>",
            page_templates={DOCS_PAGE_PATH: SCALAR_PAGE_TEMPLATE},
            path="docs",
            backend=SummitRcmFalconAsgiPlugin,
        )

    def validate(self, *args, **kwargs):
        """Singleton wrapper around the SpecTree validate() function"""
        if self.spec is None:
            return lambda _: _

        return self.spec.validate(*args, **kwargs)

    def register(self, app):
        """Singleton wrapper around the SpecTree register() function"""
        if not self.spec:
            # Load the API spec from the file
            with open(OPENAPI_JSON_PATH, "r") as api_spec_file:
                api_spec = json.load(api_spec_file)
            app.add_route("/api/openapi.json", OpenAPIAsgi(api_spec))
            app.add_route(
                self.doc_page_path,
                DocPageAsgi(
                    SCALAR_PAGE_TEMPLATE,
                    spec_url=self.spec_url,
                    spec_path=DOCS_PAGE_PATH,
                ),
            )

            syslog(f"route loaded: /{DOCS_PAGE_PATH}/docs")
        else:
            self.spec.register(app)
            syslog(f"route loaded: {self.doc_page_path}")

        if (
            ServerConfig()
            .get_parser()
            .getboolean(
                section="summit-rcm",
                option="rest_api_docs_root_redirect",
                fallback=False,
            )
        ):
            app.add_middleware(RootDocumentationRedirectMiddleware())
            syslog("route loaded: /")

    @property
    def security(self) -> dict:
        """Enabled security options for use with SpecTree validate()"""
        return {"session_token": []} if ServerConfig().sessions_enabled else {}

    @property
    def doc_page_path(self) -> str:
        """Retrieve the relative URL path to the API documentation page"""
        return "/api/docs"

    @property
    def spec_url(self) -> str:
        """Retrieve the URL to the OpenAPI JSON spec file"""
        return "/api/openapi.json"


class DummyResponse:
    """Dummy class to allow for import of spectree Response"""

    def __init__(self, *args, **kwargs):
        pass


class DocsNotEnabledException(Exception):
    """Exception to be raised when the REST API documentation is not enabled"""
