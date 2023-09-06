"""
Module to interact with system logs
"""

import os
from syslog import syslog
import falcon.asgi
from summit_rcm.services.files_service import FilesService
from summit_rcm.services.logs_service import (
    JOURNALCTL_LOG_TYPES,
    VALID_SUPPLICANT_DEBUG_LEVELS,
    JournalctlError,
    LogsService,
)


class LogsExportResource:
    """
    Resource to handle queries and requests for exporting logs
    """

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /system/logs/export endpoint
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

    async def on_get(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        GET handler for the /system/logs/data endpoint
        """
        try:
            priority = int(req.params.get("priority", 7))
            if priority not in range(0, 8, 1):
                raise ValueError("Priority must be an int between 0-7")
            days = int(req.params.get("days", 1))
            log_type = req.params.get("type", "All")
            if log_type not in JOURNALCTL_LOG_TYPES:
                raise ValueError()

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
            "suppDebugLevel": await LogsService.get_supplicant_debug_level(),
            "driverDebugLevel": LogsService.get_wifi_driver_debug_level(),
        }

    async def on_get(self, _: falcon.asgi.Request, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/logs/config endpoint
        """
        try:
            resp.media = await self.get_current_debug_levels()
            resp.content_type = falcon.MEDIA_JSON
            resp.status = falcon.HTTP_200
        except Exception as exception:
            syslog(f"Could not retrieve log configuration - {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/logs/config endpoint
        """
        try:
            put_data = await req.get_media()

            # Read in and validate the input data
            supp_level = str(put_data.get("suppDebugLevel", "")).lower()
            if not supp_level or supp_level not in VALID_SUPPLICANT_DEBUG_LEVELS:
                raise ValueError()

            drv_level = int(put_data.get("driverDebugLevel", None))
            if drv_level not in [0, 1]:
                raise ValueError()

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
