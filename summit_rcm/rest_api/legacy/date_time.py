from syslog import syslog, LOG_ERR
import falcon
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm.services.date_time_service import DateTimeService


class DateTimeSetting:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        result["zones"] = DateTimeService().zones
        result["zone"] = DateTimeService().local_zone

        success, msg = DateTimeService.check_current_date_and_time()
        if success:
            result["method"] = "auto"
            result["time"] = msg.strip()
        else:
            result["method"] = "manual"
            result["time"] = ""

        resp.media = result

    async def on_put(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }

        post_data = await req.get_media()
        zone = post_data.get("zone", "")
        method = post_data.get("method", "")
        dt = post_data.get("datetime", "")

        # Setting the timezone was initially supported when 'zone' was not an empty string so
        # re-create that here.
        if zone != "":
            try:
                await DateTimeService.set_time_zone(zone)
            except Exception as exception:
                syslog(LOG_ERR, f"Could not set timezone: {str(exception)}")
                result["InfoMsg"] = f"Could not set timezone: {str(exception)}"
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                resp.media = result
                return
        # Setting the time was initially supported when 'method' is set to 'manual' so re-create
        # that here.
        elif method == "manual" and dt != "":
            try:
                await DateTimeService.set_time_manual(dt)
            except Exception as exception:
                syslog(LOG_ERR, f"Could not set datetime: {str(exception)}")
                result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
                result["InfoMsg"] = "Could not set datetime"
                resp.media = result
                return

        # Unless we hit an error, the previous logic would return the current date and time (and
        # timezone), so re-create that here.
        success, msg = DateTimeService.check_current_date_and_time()
        if success:
            result["time"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            result["InfoMsg"] = DateTimeService().local_zone
        else:
            result["InfoMsg"] = msg
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
        resp.media = result
