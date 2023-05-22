"""
Service file to handle all HTTP configurations and executions
"""

import http.client
import time
from typing import Dict, Tuple
import ssl as SSL
from summit_rcm.utils import Singleton
from summit_rcm.utils import InProgressException
import summit_rcm.at_interface.fsm as fsm
from summit_rcm.definition import SSLModes


class HTTPService(object, metaclass=Singleton):
    """
    Service to handle HTTP configuration and executions
    """

    escape_delay: float = 0.02
    escape_count: int = 0
    escape: bool = False
    rx_timestamp: float = 0.0

    def __init__(
        self,
        host: str = "",
        port: int = 0,
        method: str = "",
        url: str = "",
        body: str = "",
        headers: Dict[str, str] = {},
        rspheader: bool = False,
        ssl: SSLModes = SSLModes.DISABLED,
        ssl_key: str = "",
        ssl_cert: str = "",
        ssl_context: SSL.SSLContext = None,
        listener: int = -1,
        timeout: int = 0,
    ) -> None:
        self.host = host
        self.port = port
        self.method = method
        self.url = url
        self.body = body
        self.headers = headers
        self.rspheader = rspheader
        self.ssl = ssl
        self.ssl_key = ssl_key
        self.ssl_cert = ssl_cert
        self.ssl_context = ssl_context
        self.listener = listener
        self.timeout = timeout

    def clear_http_configuration(self):
        """
        Resets all HTTP transaction configurations to default values
        """
        self.host = ""
        self.port = 0
        self.method = ""
        self.url = ""
        self.body = ""
        self.headers = {}
        self.rspheader = False
        self.ssl = SSLModes.DISABLED
        self.ssl_key = ""
        self.ssl_cert = ""
        self.ssl_context = None
        self.listener = -1
        self.timeout = 0

    def configure_http_transaction(
        self, host: str, port: int, method: str, url: str, timeout: int
    ) -> bool:
        """
        Sets base configurations for executing an HTTP transaction
        """
        self.clear_http_configuration()
        self.host = host
        self.port = port
        self.method = method
        self.url = url
        self.timeout = timeout

    def add_http_header(self, key: str, value: str) -> bool:
        """
        Adds or updates a header in the transaction headers dictionary
        """
        self.headers[key] = value

    def enable_response_headers(self, enabled: bool) -> bool:
        """
        Enables or disables the inclusion of headers in an HTTP response
        and returns a boolean indicating whether response headers are enabled
        """
        self.rspheader = enabled
        return self.rspheader

    def configure_http_ssl(
        self, auth_mode: int, check_hostname: bool, key: str, cert: str, ca: str
    ):
        """
        Changes status of SSL to disabled, enabled without host verification, or
        enabled with host verification and produces ssl context
        """
        try:
            context = SSL.SSLContext(SSL.PROTOCOL_TLS_CLIENT)
            context.check_hostname = check_hostname
            self.ssl = SSLModes(auth_mode)
            if self.ssl == SSLModes.NO_AUTH:
                context.verify_mode = SSL.CERT_NONE
            elif self.ssl == SSLModes.CLIENT_VERIFY_SERVER:
                context.load_default_certs()
                context.load_verify_locations(cafile=ca)
            elif self.ssl == SSLModes.SERVER_VERIFY_CLIENT:
                context.verify_mode = SSL.CERT_NONE
                context.load_cert_chain(cert, key)
            else:
                context.load_default_certs()
                context.load_verify_locations(cafile=ca)
                context.load_cert_chain(cert, key)
            self.ssl_context = context
            return
        except Exception as exception:
            self.ssl = SSLModes.DISABLED
            self.ssl_context = None
            raise exception

    def execute_http_transaction(self, length: int) -> Tuple[str, int]:
        """
        Establishes an HTTP connection and sends the configures request
        to the HTTP server and returns the HTTP response. If a length is
        given, the AT interface will enter serial data mode.
        """
        statemachine = fsm.ATInterfaceFSM()
        if self.escape:
            self.escape = False
            self.body = ""
            statemachine.deregister_listener(self.listener)
            self.listener = -1
            return ("", -1)
        transaction = (
            http.client.HTTPConnection(self.host, port=self.port, timeout=self.timeout)
            if self.ssl == SSLModes.DISABLED
            else (
                http.client.HTTPSConnection(
                    self.host,
                    port=self.port,
                    timeout=self.timeout,
                    context=self.ssl_context,
                )
            )
        )
        response_str = ""
        if len(self.body) >= length:
            self.body = self.body[:length]
            if self.listener != -1:
                statemachine.deregister_listener(self.listener)
                self.listener = -1
            transaction.request(self.method, self.url, self.body, self.headers)
            response = transaction.getresponse()
            self.body = ""
            if self.rspheader:
                for header in response.getheaders():
                    response_str += f"{header[0]}:{header[1]},"
                response_str += response_str[:-1] + "\r\n"
            response_str += response.read().decode("utf-8")
            return (response_str, length)

        def write_http_body(data: bytes):
            self.body += data.decode("utf-8")
            body_check = self.body[-3:]
            body_check_length = len(body_check)
            less_than_delay = (
                True
                if (time.time() - self.rx_timestamp) <= self.escape_delay
                else False
            )
            if not (body_check_length > 0 and body_check[-1] == "+"):
                self.escape_count = 0
            elif less_than_delay and self.escape_count != 0:
                self.escape_count += 1
                if self.escape_count == 3:
                    self.escape_count = 0
                    self.escape = True
            elif not less_than_delay:
                self.escape_count = 1
            self.rx_timestamp = time.time()

        if self.listener == -1:
            fsm.ATInterfaceFSM().at_output("> ", print_trailing_line_break=False)
            self.listener = statemachine.register_listener(write_http_body)
        raise InProgressException()
