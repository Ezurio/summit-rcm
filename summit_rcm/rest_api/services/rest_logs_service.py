#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to handle interfacing with logs for the REST API
"""

import os

try:
    from uvicorn.config import LOG_LEVELS
except ImportError as error:
    # Ignore the error if the ssl module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
    LOG_LEVELS = {}
from summit_rcm.services.logs_service import LogsService
from summit_rcm.settings import ServerConfig, SystemSettingsManage
from summit_rcm.utils import Singleton


class RESTLogsService(LogsService, metaclass=Singleton):
    """Service to handle interfacing with logs for the REST API"""

    @staticmethod
    def get_webserver_log_level() -> str | None:
        """
        Get the log level for the webserver
        """
        uvicorn_log_level = ServerConfig().uvicorn_server.config.log_level
        if isinstance(uvicorn_log_level, str):
            return uvicorn_log_level

        if isinstance(uvicorn_log_level, int):
            for log_level_string, log_level_int in LOG_LEVELS.items():
                if log_level_int == uvicorn_log_level:
                    return log_level_string

        return None

    @staticmethod
    def set_webserver_log_level(log_level: str) -> None:
        """
        Set the log level for the webserver
        """
        if log_level not in LOG_LEVELS:
            raise ValueError(f"Invalid log level: {log_level}")

        if not SystemSettingsManage.update_persistent("uvicorn_log_level", log_level):
            raise Exception(
                "Failed to update the webserver log level in the system settings"
            )

        ServerConfig().uvicorn_server.config.log_level = log_level
        ServerConfig().uvicorn_server.config.configure_logging()
