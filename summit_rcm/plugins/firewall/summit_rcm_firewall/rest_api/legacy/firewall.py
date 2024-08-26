#
# SPDX-License-Identifier: LicenseRef-Ezurio-Clause
# Copyright (C) 2024 Ezurio LLC.
#
"""
Module to support iptables firewall configuration for legacy routes.
"""

from typing import List
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm.definition import SUMMIT_RCM_ERRORS
from summit_rcm_firewall.services.firewall_service import (
    IP_VERSIONS,
    IPV4,
    PORT_COMMANDS,
    FirewallService,
    ForwardedPort,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        DefaultResponseModelLegacy,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_firewall.rest_api.utils.spectree.models import (
        ForwardedPortsResponseModelLegacy,
        ForwardedPortModelLegacy,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    DefaultResponseModelLegacy = None
    UnauthorizedErrorResponseModel = None
    ForwardedPortsResponseModelLegacy = None
    ForwardedPortModelLegacy = None
    network_tag = None


spec = SpectreeService()


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

    @spec.validate(
        resp=Response(
            HTTP_200=ForwardedPortsResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_get(self, _, resp):
        """
        Retrieve a list of ports currently forwarded via iptables firewall rules (legacy)
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

    @spec.validate(
        json=ForwardedPortModelLegacy,
        resp=Response(
            HTTP_200=DefaultResponseModelLegacy,
            HTTP_401=UnauthorizedErrorResponseModel,
        ),
        path_parameter_descriptions={"command": "The command to execute"},
        security=SpectreeService().security,
        tags=[network_tag],
        deprecated=True,
    )
    async def on_put(self, req, resp, command):
        """
        Update the list of ports currently forwarded via iptables firewall rules (legacy)
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
