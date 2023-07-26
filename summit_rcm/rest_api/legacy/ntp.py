"""
Module to support NTP configuration via chrony for legacy routes.
"""

import falcon.asgi
from summit_rcm.chrony.ntp_service import ChronyNTPService, SOURCE_COMMANDS
from summit_rcm.definition import SUMMIT_RCM_ERRORS


class NTPResourceLegacy:
    """
    Resource to expose chrony NTP configuration
    """

    @staticmethod
    def result_parameter_not_one_of(parameter: str, supplied_value: str, not_one_of):
        """
        Generate return object value for when a supplied value is not valid
        """
        return {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": f"supplied parameter '{parameter}' value {supplied_value} must be one of"
            f" {not_one_of}, ",
        }

    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /ntp endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            result["sources"] = await ChronyNTPService.chrony_get_sources()
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as exception:
            result["sources"] = []
            result["InfoMsg"] = f"Unable to retrieve chrony sources - {str(exception)}"
        resp.media = result

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response, command: str
    ) -> None:
        """
        PUT handler for the /ntp/{command} endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            post_data = await req.get_media()

            if command:
                if command not in SOURCE_COMMANDS:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, SOURCE_COMMANDS
                        )
                    )
                else:
                    await ChronyNTPService.chrony_configure_sources(
                        command, post_data.get("sources", [])
                    )
                    result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"
        except Exception as exception:
            result["InfoMsg"] = f"Unable to update chrony sources - {str(exception)}"

        resp.media = result
