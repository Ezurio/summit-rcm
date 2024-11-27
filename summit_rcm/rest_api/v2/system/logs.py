#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to interact with system logs
"""

import os
from syslog import syslog
import falcon.asgi

try:
    from uvicorn.config import LOG_LEVELS
except ImportError as error:
    # Ignore the error if the ssl module is not available if generating documentation
    if os.environ.get("DOCS_GENERATION") != "True":
        raise error
    LOG_LEVELS = {}
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import (
    DriverLogLevelEnum,
    JournalctlLogTypesEnum,
    SupplicantLogLevelEnum,
)
from summit_rcm.services.files_service import FilesService
from summit_rcm.services.logs_service import (
    JournalctlError,
)
from summit_rcm.rest_api.services.rest_logs_service import (
    RESTLogsService as LogsService,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        BadRequestErrorResponseModel,
        InternalServerErrorResponseModel,
        LogVerbosity,
        LogsDataRequestQuery,
        LogsDataResponseModel,
        LogsExportRequestModel,
        UnauthorizedErrorResponseModel,
        WebserverLogLevel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import system_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    BadRequestErrorResponseModel = None
    InternalServerErrorResponseModel = None
    LogVerbosity = None
    LogsDataRequestQuery = None
    LogsDataResponseModel = None
    LogsExportRequestModel = None
    UnauthorizedErrorResponseModel = None
    WebserverLogLevel = None
    system_tag = None


spec = SpectreeService()


class LogsExportResource:
    """
    Resource to handle queries and requests for exporting logs
    """

    @spec.validate(
        json=LogsExportRequestModel,
        resp=Response(
            HTTP_200=None,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Retrieve a password-protected zip archive of the journal logs
        """
        archive = ""
        try:
            get_data = await req.get_media()
            password = get_data.get("password", "")
            if not password:
                resp.status = falcon.HTTP_400
                return

            success, msg, archive = FilesService.export_logs(password)
            if not success:
                raise Exception(msg)

            resp.stream = await FilesService.handle_file_download(archive)
            resp.content_type = falcon.MEDIA_TEXT
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not export logs - {str(exception)}")
            resp.status = falcon.HTTP_500
        finally:
            if os.path.isfile(archive):
                os.unlink(archive)


class LogsDataResource:
    """
    Resource to handle queries and requests for retrieving journal log data
    """

    @spec.validate(
        query=LogsDataRequestQuery,
        resp=Response(
            HTTP_200=LogsDataResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Retrieve journal log data
        """
        try:
            priority = int(req.params.get("priority", 7))
            if priority not in range(0, 8, 1):
                raise ValueError("Priority must be an int between 0-7")
            days = int(req.params.get("days", 1))
            log_type = JournalctlLogTypesEnum(req.params.get("type", "All"))

            resp.media = LogsService.get_journal_log_data(
                log_type=log_type, priority=priority, days=days
            )
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except ValueError:
            resp.status = falcon.HTTP_400
        except JournalctlError as error:
            syslog(
                "Could not retrieve log data, journalctl error - "
                f"{str(error.return_code)}: {str(error)}"
            )
            resp.status = falcon.HTTP_500
        except Exception as exception:
            syslog(f"Could not retrieve log data - {str(exception)}")
            resp.status = falcon.HTTP_500


class LogsConfigResource:
    """
    Resource to handle queries and requests for configuring the debug level for the supplicant and
    Wi-Fi driver
    """

    async def get_current_debug_levels(self) -> dict:
        """Retrieve the current debug levels for the supplicant and Wi-Fi driver"""
        return {
            "suppDebugLevel": (await LogsService.get_supplicant_debug_level()).value,
            "driverDebugLevel": LogsService.get_wifi_driver_debug_level().value,
        }

    @spec.validate(
        resp=Response(
            HTTP_200=LogVerbosity,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current log verbosity levels for the supplicant and Wi-Fi driver
        """
        try:
            resp.media = await self.get_current_debug_levels()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve log configuration - {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=LogVerbosity,
        resp=Response(
            HTTP_200=LogVerbosity,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Set the log verbosity levels for the supplicant and Wi-Fi driver
        """
        try:
            put_data = await req.get_media()

            # Read in and validate the input data
            supp_level = SupplicantLogLevelEnum(
                put_data.get("suppDebugLevel", "").lower()
            )
            if not supp_level:
                raise ValueError()

            drv_level = DriverLogLevelEnum(put_data.get("driverDebugLevel", None))

            # Configure new values
            await LogsService.set_supplicant_debug_level(supp_level)
            LogsService.set_wifi_driver_debug_level(drv_level)

            # Return newly-set current configuration
            resp.media = await self.get_current_debug_levels()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except (ValueError, TypeError):
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(f"Could not set log configuration - {str(exception)}")
            resp.status = falcon.HTTP_500


class LogsWebserverResource:
    """
    Resource to handle queries and requests for configuring the webserver log level
    """

    @spec.validate(
        resp=Response(
            HTTP_200=WebserverLogLevel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        Retrieve current webserver log level

        Possible webserverLogLevel options:
        - "critical"
        - "error" (default)
        - "warning"
        - "info"
        - "debug"
        - "trace"
        """
        try:
            resp.media = {"webserverLogLevel": LogsService.get_webserver_log_level()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve webserver log level - {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=WebserverLogLevel,
        resp=Response(
            HTTP_200=WebserverLogLevel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[system_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Set the current webserver log level

        Possible webserverLogLevel options:
        - "critical"
        - "error" (default)
        - "warning"
        - "info"
        - "debug"
        - "trace"
        """
        try:
            put_data = await req.get_media()

            # Read in and validate the input data
            webserver_log_level = put_data.get("webserverLogLevel", "")
            if not webserver_log_level or webserver_log_level not in LOG_LEVELS:
                raise ValueError()

            # Configure new log level
            LogsService.set_webserver_log_level(str(webserver_log_level))

            # Return newly-set current configuration
            resp.media = {"webserverLogLevel": LogsService.get_webserver_log_level()}
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except (ValueError, TypeError):
            syslog(f"Invalid webserver log level: {webserver_log_level}")
            resp.status = falcon.HTTP_400
        except Exception as exception:
            syslog(f"Could not set webserver log level - {str(exception)}")
            resp.status = falcon.HTTP_500
