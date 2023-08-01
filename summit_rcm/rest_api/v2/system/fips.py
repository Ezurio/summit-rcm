"""
Module to support FIPS configuration for v2 routes
"""

import falcon
from summit_rcm.services.fips_service import FipsService, VALID_FIPS_STATES


class FipsResource(object):
    """
    Resource to handle FIPS state queries and requests
    """

    async def on_get(self, req: falcon.Request, resp: falcon.Response) -> None:
        """
        GET handler for the /system/fips endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        fips_state = await FipsService().get_fips_state()

        # Change from snake case to camel case for the 'fips_wifi' case
        if fips_state == "fips_wifi":
            fips_state = "fipsWifi"

        resp.media = {"state": fips_state}

    async def on_put(self, req: falcon.Request, resp: falcon.Response) -> None:
        """
        PUT handler for the /system/fips endpoint
        """
        post_data = await req.get_media()
        desired_state = str(post_data.get("state", ""))

        # Change from camel case to snake case for the 'fipsWifi' case
        if desired_state == "fipsWifi":
            desired_state = "fips_wifi"

        if desired_state == "" or desired_state not in VALID_FIPS_STATES:
            resp.status = falcon.HTTP_400
            return

        success: bool = await FipsService().set_fips_state(desired_state)

        new_fips_state = await FipsService().get_fips_state()

        # Change from snake case to camel case for the 'fips_wifi' case
        if new_fips_state == "fips_wifi":
            new_fips_state = "fipsWifi"

        resp.status = falcon.HTTP_200 if success else falcon.HTTP_500
        resp.content_type = falcon.MEDIA_JSON
        resp.media = {"state": new_fips_state}
