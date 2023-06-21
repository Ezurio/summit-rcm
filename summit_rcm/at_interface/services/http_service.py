"""
Service file to handle all HTTP configurations and executions
"""

import http.client
from typing import Dict
from summit_rcm.utils import Singleton
from summit_rcm.utils import InProgressException
import summit_rcm.at_interface.fsm as fsm


class HTTPService(object, metaclass=Singleton):
    """
    Handles HTTP Configuration and Executions
    """

    def __init__(
        self,
        host: str = "",
        port: int = 0,
        method: str = "",
        url: str = "",
        body: str = "",
        headers: Dict[str, str] = {},
        rspheader: bool = False,
        ssl: int = 0,
        ssl_ca: list = [],
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
        self.ssl_ca = ssl_ca
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
        self.ssl = 0
        self.ssl_ca = []
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

    def enable_response_headers(self, enabled: bool) -> str:
        """
        Enables or disables the inclusion of headers in an HTTP response
        and returns a boolean indicating whether response headers are enabled
        """
        self.rspheader = enabled
        return str(self.rspheader)

    def execute_http_transaction(self, length: int) -> str:
        """
        Establishes an HTTP connection and sends the configures request
        to the HTTP server and returns the HTTP response. If a length is
        given, the AT interface will enter serial data mode.
        """
        statemachine = fsm.ATInterfaceFSM()
        transaction = http.client.HTTPConnection(
            self.host, port=self.port, timeout=self.timeout
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
                    response_str = f"{header[0]}:{header[1]},"
                response_str += response_str[:-1] + "\r\n"
            response_str += response.read().decode("utf-8")
            return response_str

        def write_http_body(data: bytes):
            self.body += data.decode("utf-8")

        if self.listener == -1:
            fsm.ATInterfaceFSM().dte_output("\r\n> ")
            self.listener = statemachine.register_listener(write_http_body)
        raise InProgressException()
