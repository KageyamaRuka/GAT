import asyncio
from typing import Any
from typing import List

from mitmproxy import options
from mitmproxy.tools import dump


class Mitm:
    def __init__(self, host: str, port: int, addons: List[Any]) -> None:
        self.host = host
        self.port = port
        self.addons = addons

    def worker(self):
        event_loop = asyncio.get_event_loop()
        event_loop.run_until_complete(self.start_proxy())

    async def start_proxy(self):
        opts = options.Options(listen_host=self.host, listen_port=self.port)

        master = dump.DumpMaster(
            opts,
            with_termlog=False,
            with_dumper=False,
        )
        for addon in self.addons:
            master.addons.add(addon())

        await master.run()
        return master
