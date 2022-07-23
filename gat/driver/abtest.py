import multiprocessing

from driver import Executor
from utility.mitm import Mitm


class ABTest(Executor):
    def __init__(self, config, task):
        self.task = task
        self.mitm_host = (
            self.task.app.mitm_host
            if self.task.app.mitm_host is not None
            else "0.0.0.0"
        )
        self.mitm_port = (
            self.task.app.mitm_port
            if self.task.app.mitm_port is not None
            else 8080
        )
        super().__init__()
        self.log(f"ABTest driver get config {config}")
        self.sequential()

    def start_mitm(self, addons):
        self.mitm = Mitm(
            host=self.mitm_host,
            port=self.mitm_port,
            addons=addons,
        )
        self.mitm_process = multiprocessing.Process(target=self.mitm.worker)
        self.mitm_process.start()

    def stop_mitm(self):
        self.mitm_process.kill()
