"""
Module to support iptables firewall configuration for v2 routes.
"""

from syslog import LOG_ERR, syslog
from typing import List
import falcon.asgi
from summit_rcm.settings import ServerConfig
from summit_rcm.rest_api.services.spectree_service import (
    DocsNotEnabledException,
    SpectreeService,
)
from summit_rcm_firewall.services.firewall_service import (
    ADD_PORT,
    REMOVE_PORT,
    FirewallService,
    ForwardedPort,
)

try:
    if not ServerConfig().rest_api_docs_enabled:
        raise DocsNotEnabledException()

    from spectree import Response
    from summit_rcm.rest_api.utils.spectree.models import (
        InternalServerErrorResponseModel,
        BadRequestErrorResponseModel,
        UnauthorizedErrorResponseModel,
    )
    from summit_rcm_firewall.rest_api.utils.spectree.models import (
        ForwardedPortsResponseModel,
    )
    from summit_rcm.rest_api.utils.spectree.tags import network_tag
except (ImportError, DocsNotEnabledException):
    from summit_rcm.rest_api.services.spectree_service import DummyResponse as Response

    InternalServerErrorResponseModel = None
    BadRequestErrorResponseModel = None
    UnauthorizedErrorResponseModel = None
    ForwardedPortsResponseModel = None
    network_tag = None


spec = SpectreeService()


class FirewallForwardedPortsResource:
    """
    Resource to handle queries and requests for ports forwarded via iptables firewall rules
    """

    @staticmethod
    def forwarded_port_in_put_data(
        put_data: List[dict], forwarded_port: ForwardedPort
    ) -> bool:
        """
        Check whether or not the incoming JSON-encoded list of forwarded ports contains the
        specified forwarded port
        """
        for put_data_forwarded_port in put_data:
            if (
                ForwardedPort(
                    put_data_forwarded_port["port"],
                    put_data_forwarded_port["protocol"],
                    put_data_forwarded_port["toport"],
                    put_data_forwarded_port["toaddr"],
                    put_data_forwarded_port["ipVersion"],
                )
                == forwarded_port
            ):
                return True
        return False

    @spec.validate(
        resp=Response(
            HTTP_200=ForwardedPortsResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        Retrieve a list of ports currently forwarded via iptables firewall rules
        """
        try:
            resp.media = [
                x.to_json(is_legacy=False) for x in FirewallService().forwarded_ports
            ]
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to retrieve forwarded ports: {str(exception)}")
            resp.status = falcon.HTTP_500

    @spec.validate(
        json=ForwardedPortsResponseModel,
        resp=Response(
            HTTP_200=ForwardedPortsResponseModel,
            HTTP_400=BadRequestErrorResponseModel,
            HTTP_401=UnauthorizedErrorResponseModel,
            HTTP_500=InternalServerErrorResponseModel,
        ),
        security=SpectreeService().security,
        tags=[network_tag],
    )
    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        Update the list of ports currently forwarded via iptables firewall rules
        """
        try:
            put_data = await req.get_media()
            if put_data is None or not isinstance(put_data, list):
                resp.status = falcon.HTTP_400
                return

            # Collect a list of forwarded ports we need to add (ports NOT currently set which need
            # to be). If we find one, add it. At the same time, also verify the input data is
            # properly formatted.
            for forwarded_port_in in put_data:
                if not isinstance(forwarded_port_in, dict):
                    resp.status = falcon.HTTP_400
                    return

                forwarded_port_in_keys = forwarded_port_in.keys()
                if (
                    "port" not in forwarded_port_in_keys
                    or "protocol" not in forwarded_port_in_keys
                    or "toport" not in forwarded_port_in_keys
                    or "toaddr" not in forwarded_port_in_keys
                    or "ipVersion" not in forwarded_port_in_keys
                ):
                    resp.status = falcon.HTTP_400
                    return

                new_forwarded_port = ForwardedPort(
                    forwarded_port_in["port"],
                    forwarded_port_in["protocol"],
                    forwarded_port_in["toport"],
                    forwarded_port_in["toaddr"],
                    forwarded_port_in["ipVersion"],
                )

                if not FirewallService().forwarded_port_is_present(new_forwarded_port):
                    await FirewallService().configure_forwarded_port(
                        ADD_PORT, new_forwarded_port
                    )

            # Collect a list of forwarded ports we need to remove (ports currently set which need
            # to be REMOVED). If we find one, remove it.
            for current_forwarded_port in FirewallService().forwarded_ports:
                if not self.forwarded_port_in_put_data(
                    put_data=put_data, forwarded_port=current_forwarded_port
                ):
                    await FirewallService().configure_forwarded_port(
                        REMOVE_PORT, current_forwarded_port
                    )

            resp.media = [
                x.to_json(is_legacy=False) for x in FirewallService().forwarded_ports
            ]
            resp.status = falcon.HTTP_200
            resp.content_type = falcon.MEDIA_JSON
        except Exception as exception:
            syslog(LOG_ERR, f"Unable to configure forwarded ports: {str(exception)}")
            resp.status = falcon.HTTP_500
