#!/usr/bin/python
#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2025 Ezurio LLC.
#
"""Generate the OpenAPI spec for the Summit RCM REST API."""

import asyncio
import json
import os
import sys
from pathlib import Path

import falcon.asgi

os.environ["DOCS_GENERATION"] = "True"


REPO_ROOT = Path(__file__).resolve().parent
PLUGINS_ROOT = REPO_ROOT / "summit_rcm" / "plugins"

os.environ.setdefault("SUMMIT_RCM_SERVER_CONF_FILE", str(REPO_ROOT / "summit-rcm.ini"))
os.environ.setdefault(
    "SUMMIT_RCM_SETTINGS_FILE", str(REPO_ROOT / "summit-rcm-settings.txt")
)


def _plugin_search_paths() -> list[str]:
    return [str(path) for path in PLUGINS_ROOT.iterdir() if path.is_dir()]


def _prepare_plugin_import_path() -> list[str]:
    plugin_paths = _plugin_search_paths()
    for path in reversed(plugin_paths):
        if path not in sys.path:
            sys.path.insert(0, path)
    return plugin_paths


async def _load_builtin_routes(summit_rcm_module) -> None:
    await summit_rcm_module.add_definitions_legacy()
    await summit_rcm_module.add_users_legacy()
    await summit_rcm_module.add_network_v2()
    await summit_rcm_module.add_network_legacy()
    await summit_rcm_module.add_advanced_legacy()
    await summit_rcm_module.add_certificates_legacy()
    await summit_rcm_module.add_files_legacy()
    await summit_rcm_module.add_date_time_legacy()
    await summit_rcm_module.add_logs_legacy()
    await summit_rcm_module.add_version_legacy()
    await summit_rcm_module.add_firmware_legacy()
    await summit_rcm_module.add_system_v2()
    await summit_rcm_module.add_login_v2()


async def _load_plugin_routes(summit_rcm_module) -> None:
    for module in summit_rcm_module.discovered_plugins.values():
        if hasattr(module, "get_legacy_routes"):
            for route, resource in (await module.get_legacy_routes()).items():
                summit_rcm_module.add_route(route, resource)

        if hasattr(module, "get_v2_routes"):
            for route, resource in (await module.get_v2_routes()).items():
                summit_rcm_module.add_route(route, resource)


async def _build_app():
    plugin_paths = _prepare_plugin_import_path()

    import summit_rcm
    from summit_rcm.rest_api.services.spectree_service import SpectreeService

    summit_rcm.app = falcon.asgi.App()
    summit_rcm.summit_rcm_plugins = []
    summit_rcm.discover_plugins(path=plugin_paths)

    await _load_builtin_routes(summit_rcm)
    await _load_plugin_routes(summit_rcm)
    SpectreeService().register(summit_rcm.app)

    return summit_rcm.app, SpectreeService()


def generate_docs():
    """Generate the OpenAPI spec for the Summit RCM REST API."""
    _, spectree_service = asyncio.run(_build_app())
    if spectree_service.spec is None:
        raise RuntimeError("OpenAPI generation is not active")

    openapi_json_file_path = os.environ.get(
        "OPENAPI_JSON_PATH", "summit-rcm-openapi.json"
    )
    with open(openapi_json_file_path, "w") as openapi_json_file:
        json.dump(spectree_service.spec.spec, openapi_json_file)

    print(f"Summit RCM OpenAPI spec generated: {openapi_json_file_path}")


if __name__ == "__main__":
    generate_docs()
