import cherrypy
from ws4py.websocket import WebSocket

from .bt_ble import ble_notification_objects
from .. import definition


class BluetoothWebsocket(object):
    @cherrypy.tools.json_out()
    @cherrypy.expose
    def index(self):
        result = {
            "SDCERR": definition.SUMMIT_RCM_ERRORS["SDCERR_SUCCESS"],
            "InfoMsg": "",
        }
        return result

    @cherrypy.expose
    def ws(self):
        # see BluetoothWebSocketHandler
        pass


class BluetoothWebSocketHandler(WebSocket):
    def __init__(self, *args, **kwargs):
        ble_notification_objects.append(self)
        super(BluetoothWebSocketHandler, self).__init__(*args, kwargs)

    def __del__(self):
        if self in ble_notification_objects:
            ble_notification_objects.remove(self)

    def received_message(self, message):
        """
        Called whenever a complete ``message``, binary or text,
        is received and ready for application's processing.

        The passed message is an instance of :class:`messaging.TextMessage`
        or :class:`messaging.BinaryMessage`.
        """
        pass

    def ble_notify(self, message):
        if (
            self.connection
            and not self.client_terminated
            and not self.server_terminated
        ):
            try:
                self.send(message, binary=False)
            except Exception as e:
                cherrypy.log("BluetoothWebSocketHandler:" + str(e))
                self.close(reason=str(e))
                self.close_connection()
                self.terminate()
                self.__del__()
