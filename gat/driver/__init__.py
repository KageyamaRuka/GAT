import threading
from datetime import datetime
from functools import partial
from typing import Any
from typing import List

import gevent
from model.case import Case
from utility import elog_deco
from utility import tlog


class Executor:
    def __init__(self):
        self.result: List[Case] = (
            self.task.result if self.task is not None else None
        )
        self.data: dict[str, Any] = {}
        self.closed = False
        self.log_path: str = (
            self.task.log_path if self.task is not None else None
        )
        self.log = partial(tlog, log_path=self.log_path)

    def close(self):
        self.closed = True

    def sleep(self, timeout):
        self.log(f"sleep {timeout} seconds")
        gevent.sleep(timeout)

    def sequential(self):
        if not self.task or not self.task.case:
            return
        while True:
            try:
                self.case: Case = self.task.case.pop(0)
                self.log(f"Driver get case {self.case}")
                self.execute()
                self.log(f"case finished {self.case}")
            except IndexError:
                print(f"{threading.current_thread().name} task clear")
                return

    def execute(self):
        self.case.status = "running"
        for op in self.case.operations:
            self.log(f"get op {op}")
            for k, v in op.items():
                try:
                    api = getattr(self, k)
                except AttributeError as e:
                    self.log(f"Get api {k} failed")
                    self.case.status = "failed"
                    self.case.failed_reason = {
                        k: [
                            arg.replace("\n", "") if type(arg) is str else arg
                            for arg in e.args
                        ],
                    }
                    self.result.append(self.case)
                    self.close_app()
                    return
                self.log(f"get api {api}")
                start_time = datetime.now()
                self.data["start_time"] = start_time
                api_deco = elog_deco(self.log_path)(api)
                try:
                    api_deco(**v) if v else api_deco()
                except Exception as e:
                    self.log(f"Execute api {api} failed")
                    end_time = datetime.now()
                    start_time = self.data.get("start_time")
                    if start_time:
                        duration = end_time - start_time
                        self.log(
                            f"""Time cost
                            {duration.seconds} seconds,
                            {duration.microseconds} microseconds
                            """,
                        )
                    self.case.status = "failed"
                    self.case.failed_reason = {
                        k: [
                            arg.replace("\n", "<br>").replace("\\", "")
                            if type(arg) is str
                            else arg
                            for arg in e.args
                        ],
                    }
                    self.result.append(self.case)
                    tlog(
                        f"{threading.current_thread().name} case {self.case.id} {self.case.name} failed",
                    )
                    self.close()
                    return
                else:
                    self.log(f"api {api} passed")
        self.case.status = "pass"
        self.result.append(self.case)
        tlog(
            f"{threading.current_thread().name} case {self.case.id} {self.case.name} pass",
        )
        self.close()
