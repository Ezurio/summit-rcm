"""
Module to support iptables firewall configuration for legacy routes.
"""

from typing import List
import falcon.asgi
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm_firewall.services.firewall_service import (
    IP_VERSIONS,
    IPV4,
    PORT_COMMANDS,
    FirewallService,
    ForwardedPort,
)


class FirewallResourceLegacy:
    """
    Resource to expose iptables firewall configuration
    """

    @staticmethod
    def check_parameters(post_data, parameters: List[str]):
        """
        Verify required parameters are present in the provided post data. If not, raise a ValueError
        exception.
        """
        for parameter in parameters:
            if parameter not in post_data:
                raise ValueError(f"required parameter '{parameter}' not specified")

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

    async def on_get(self, _, resp):
        """
        GET handler for the /firewall endpoint
        """
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_JSON
        result = {
            "SDCERR": SUMMIT_RCM_ERRORS["SDCERR_FAIL"],
            "InfoMsg": "",
        }

        try:
            result["Forward"] = [
                x.to_json(is_legacy=True) for x in FirewallService().forwarded_ports
            ]
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
        except Exception as exception:
            FirewallService.log_exception(exception)
            result["InfoMsg"] = f"Error: {str(exception)}"
        resp.media = result

    async def on_put(self, req, resp, command):
        """
        PUT handler for the /firewall/{command} endpoint
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
                if command not in PORT_COMMANDS:
                    result.update(
                        self.result_parameter_not_one_of(
                            "command", command, PORT_COMMANDS
                        )
                    )
                else:
                    self.check_parameters(
                        post_data, ["port", "protocol", "toport", "toaddr"]
                    )
                    port = post_data["port"]
                    protocol = post_data["protocol"]
                    toport = post_data["toport"]
                    toaddr = post_data["toaddr"]
                    ip_version = post_data.get("ip_version", None)
                    if ip_version and ip_version not in IP_VERSIONS:
                        result.update(
                            self.result_parameter_not_one_of(
                                "ip_version", ip_version, IP_VERSIONS
                            )
                        )
                        resp.media = result
                        return
                    success, msg = await FirewallService().configure_forwarded_port(
                        command,
                        ForwardedPort(
                            port,
                            protocol,
                            toport,
                            toaddr,
                            ip_version if ip_version else IPV4,
                        ),
                    )
                    result["InfoMsg"] = msg
                    if success:
                        result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"]
            else:
                result["InfoMsg"] = "No command specified"
        except Exception as exception:
            result["SDCERR"] = SUMMIT_RCM_ERRORS["SDCERR_FAIL"]
            FirewallService.log_exception(exception)
            result["InfoMsg"] = f"Error: {str(exception)}"

        resp.media = result
