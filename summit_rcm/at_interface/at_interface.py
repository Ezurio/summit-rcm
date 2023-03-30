import asyncio
from syslog import LOG_ERR, syslog
import threading
from summit_rcm.at_interface.fsm import ATInterfaceFSM


class ATInterface:
    def __init__(self) -> None:
        self.loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()

    def start(self):
        fd = ATInterfaceFSM().dte_file.fileno()
        self.loop.add_reader(fd, self.reader)
        self.loop.call_later(0.1, self.repeat)
        try:
            threading.Thread(target=self.loop.run_forever, daemon=True).start()
        except Exception as e:
            syslog(LOG_ERR, f"ATInterface error: {str(e)}")

    def repeat(self):
        ATInterfaceFSM().check_escape()
        self.loop.call_later(0.1, self.repeat)
        if ATInterfaceFSM().quit:
            self.loop.stop()

    def reader(self):
        b = ATInterfaceFSM().dte_file.read(1024)
        ATInterfaceFSM().input_received(message=b)
