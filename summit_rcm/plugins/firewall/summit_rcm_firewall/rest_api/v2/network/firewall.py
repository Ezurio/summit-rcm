"""
Module to support iptables firewall configuration for v2 routes.
"""

from syslog import LOG_ERR, syslog
from typing import List
import falcon.asgi
from summit_rcm_firewall.services.firewall_service import (
    ADD_PORT,
    REMOVE_PORT,
    FirewallService,
    ForwardedPort,
)


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

    async def on_get(self, _, resp: falcon.asgi.Response) -> None:
        """
        GET handler for the /network/firewall/forwardedPorts endpoint
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

    async def on_put(
        self, req: falcon.asgi.Request, resp: falcon.asgi.Response
    ) -> None:
        """
        PUT handler for the /network/firewall/forwardedPorts endpoint
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
