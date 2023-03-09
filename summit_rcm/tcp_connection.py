import socket
import threading
from syslog import syslog
from typing import Optional

TCP_PORT_MIN: int = 1025
# Keep away from dynamic ports, 49152 to 65535
TCP_PORT_MAX: int = 49152 - 1

TCP_SOCKET_HOST = "0.0.0.0"
SOCK_TIMEOUT = 5
""" Interval to monitor socket for errors or closure in seconds """


class TcpConnection(object):
    """Represent a TCP server socket connection."""

    def __init__(self):
        self._tcp_lock = threading.Lock()
        self._tcp_connection: Optional[socket.socket] = None
        self.port: Optional[int] = None

    @staticmethod
    def validate_port(port: int) -> bool:
        """
        :rtype: bool
        :param port: port number to validate
        :return: true if port falls within valid range; false otherwise
        """
        try:
            return TCP_PORT_MIN <= int(port) <= TCP_PORT_MAX
        except Exception:
            return False

    def tcp_server(self, host, params) -> socket.socket:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        port = int(params["tcpPort"])
        self.port = port
        server_address = (host, port)
        sock.bind(server_address)
        sock.listen()
        return sock

    def stop_tcp_server(self, sock: socket.SOCK_STREAM):
        """Stop the specified TCP server.  Note that if accept() is used, it will block
        indefinitely if the socket is closed, unless a timeout is applied to the socket,
        and OSError with socket.EBADF handled in case of closure.
        """
        self.close_tcp_connection()
        if sock:
            sock.close()

    def close_tcp_connection(self):
        # Create local reference for thread-safety
        tcp_connection = self._tcp_connection
        if tcp_connection:
            try:
                tcp_connection.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                # If the connection is not open, ignore.
                if (
                    e.errno != socket.EBADF
                    and e.strerror != "Transport endpoint is not connected"
                ):
                    syslog("TcpConnection.close_tcp_connection:" + str(e))
            try:
                tcp_connection.close()
            except OSError as e:
                if e.errno != socket.EBADF:
                    syslog("TcpConnection.close_tcp_connection:" + str(e))

    def tcp_connection_try_send(self, data_encoded):
        """
        Try to send the supplied data over the tcp connection, ignoring all
        errors, for use in cases where connection may have dropped and
        it is tolerable to not send data.
        :param data_encoded: encoded data to be sent
        :return:
        """
        with self._tcp_lock:
            if self._tcp_connection:
                try:
                    self._tcp_connection.sendall(data_encoded)
                except Exception:
                    pass
