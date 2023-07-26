"""
Module to support NTP configuration via chrony for v2 routes.
"""

from syslog import LOG_ERR, syslog
import falcon.asgi
from summit_rcm.chrony.ntp_service import (
    REMOVE_SOURCE,
    OVERRIDE_SOURCES,
    ChronyNTPService,
)


class NTPSourcesResource:
    """
    Resource to handle queries and requests for chrony NTP sources
    """

    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /system/datetime/ntp endpoint
        """
        try:
            resp.media = await ChronyNTPService.chrony_get_sources()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve chrony NTP sources: {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /system/datetime/ntp endpoint
        """
        try:
            put_data = await req.get_media(default_when_empty=None)
            if put_data is None or not isinstance(put_data, list):
                resp.status = falcon.HTTP_400
                return

            new_sources: list[str] = []
            for source in put_data:
                if not isinstance(source, dict):
                    resp.status = falcon.HTTP_400
                    return

                source_keys = source.keys()
                if "address" not in source_keys or "type" not in source_keys:
                    resp.status = falcon.HTTP_400
                    return

                # Only 'static' sources (e.g., sources not configured via DHCP) can be configured
                if source["type"] == "static":
                    new_sources.append(str(source["address"]))
            await ChronyNTPService.chrony_configure_sources(
                OVERRIDE_SOURCES, new_sources
            )

            resp.media = await ChronyNTPService.chrony_get_sources()
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to configure chrony NTP sources: {str(exception)}")
            resp.status = falcon.HTTP_500


class NTPSourceResource:
    """
    Resource to handle queries and requests for a specific chrony NTP source by address
    """

    async def on_get(self, _, resp: falcon.asgi.Response, address: str) -> None:
        """
        GET handler for the /system/datetime/ntp/{address} endpoint
        """
        try:
            if not address:
                resp.status = falcon.HTTP_400
                return

            for source in await ChronyNTPService.chrony_get_sources():
                if source["address"] == address:
                    resp.media = {"address": source["address"], "type": source["type"]}
                    resp.status = falcon.HTTP_200
                    resp.content_type = falcon.MEDIA_JSON
                    return

            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve chrony NTP source: {str(exception)}")
            resp.status = falcon.HTTP_500

    async def on_delete(
        self, _: falcon.asgi.Request, resp: falcon.asgi.Response, address: str
    ) -> None:
        """
        DELETE handler for the /system/datetime/ntp/{address} endpoint
        """
        try:
            if not address:
                resp.status = falcon.HTTP_400
                return

            for source in await ChronyNTPService.chrony_get_sources():
                # Only 'static' sources (e.g., sources not configured via DHCP) can be removed
                if source["address"] == address and source["type"] == "static":
                    await ChronyNTPService.chrony_configure_sources(
                        REMOVE_SOURCE, [source["address"]]
                    )
                    resp.status = falcon.HTTP_200
                    return

            resp.status = falcon.HTTP_404
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to remove chrony NTP source: {str(exception)}")
            resp.status = falcon.HTTP_500
