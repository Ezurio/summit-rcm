import falcon
from summit_rcm.services.version_service import VersionService
from summit_rcm import definition


class Version:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        try:
            version = await VersionService().get_version(is_legacy=True)
            version["SDCERR"] = definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            version["InfoMsg"] = ""
        except Exception as e:
            version = {
                "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
                "InfoMsg": f"An exception occurred while trying to get versioning info: {e}",
            }
        resp.media = version
