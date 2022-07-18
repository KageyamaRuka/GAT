import gevent
import re
import requests
import threading
from datetime import datetime
from functools import partial
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from gat.model.case import Case
from gat.model.task import Task
from gat.utility import elog_deco
from gat.utility import tlog
from gat.utility import yaml_dumper
from gat.utility import yaml_loader


class HttpDriver:
    performance_result: list[dict[str, dict[str, str]]] = []
    api: set[str] = set()

    def __init__(self, config: Dict, task: Optional[Task]):
        self.debug = config.get("debug", False)
        self.headers: dict[str, str] = {}
        self.data: dict[str, Any] = {}
        self.name = config.get("device_id")
        self.log_path: str = task.log_path if task is not None else None
        self.log = partial(tlog, log_path=self.log_path)
        self.index = int(self.name.split("-")[-1])
        self.log(f"Thread {self.name} Config get {config}")
        self.task = task
        self.result: List[Case] = task.result if task is not None else None
        self.closed = False
        self.config = config

        while True:
            self.session = requests.Session()
            self.session.trust_env = False
            if not task:
                return
            try:
                self.case: Case = task.case.pop(0)
                self.log(f"Driver get case {self.case}")
                self.execute()
                self.log(f"case finished {self.case}")
            except IndexError:
                print(f"{threading.current_thread().name} task clear")
                performance_info = yaml_loader(
                    f"{self.log_path}/performance.yaml",
                )
                if performance_info is None:
                    performance_info = self.performance_result
                else:
                    performance_info.extend(self.performance_result)
                yaml_dumper(
                    info=performance_info,
                    file_path=f"{self.log_path}/performance.yaml",
                )
                api_info = yaml_loader(f"{self.log_path}/api.yaml")
                if api_info is None:
                    api_info = self.api
                else:
                    api_info.extend(self.api)
                yaml_dumper(
                    info=api_info,
                    file_path=f"{self.log_path}/api.yaml",
                )
                return

    def http(
        self,
        path=None,
        url=None,
        method="GET",
        headers=None,
        params=None,
        json=None,
        timeout=60,
        break_on_failure=True,
        error_code=None,
        **kwargs,
    ):
        self.log(f"break_on_failure {break_on_failure}")
        if headers is not None:
            self.headers.update(headers)
        self.log(f"Try to request {method} {url}{path}")
        start_time = datetime.now()
        self.data["start_time"] = start_time
        self.data["method"] = method
        self.data["url"] = url
        self.data["path"] = path
        resp = self.session.request(
            method=method,
            url=f"{url}{path}" if path is not None else url,
            headers=self.headers,
            params=params,
            json=json,
            timeout=timeout,
            cookies=self.session.cookies,
            **kwargs,
        )
        end_time = datetime.now()
        duration = end_time - start_time
        self.log(
            f"""Time cost
            {duration.seconds} seconds,
            {duration.microseconds} microseconds
            """,
        )
        self.performance_result.append(
            {
                f"{self.name} {method} {url}{path}": {
                    "duration": f"""
                    {duration.seconds}-seconds-
                    {duration.microseconds // 1000}-milliseconds-
                    {duration.microseconds % 1000}-microseconds
                    """,
                },
            },
        )
        self.api.add(re.sub(r"\d{2,20}", "*", f"{url}{path}", count=10))

        if error_code is None:
            if resp.status_code not in range(200, 205):
                if break_on_failure is True:
                    raise Exception(
                        f"""
                        Error: {resp.status_code} \n
                        resp {resp.text} \n
                        for request {method} url {resp.request.url} \n
                        headers {resp.request.headers} \n
                        body {resp.request.body}
                        """,
                    )
                self.log(
                    f"""
                    Error: {resp.status_code} \n
                    resp {resp.text} \n
                    for request {method} url {resp.request.url} \n
                    headers {resp.request.headers} \n
                    body {resp.request.body}""",
                )
                return resp
            else:
                if self.debug:
                    self.log(
                        f"""
                        Success {resp.status_code} \n
                        resp {resp.text} \n
                        for request {method} url {resp.request.url} \n
                        headers {resp.request.headers} \n
                        body {resp.request.body}""",
                    )
                else:
                    self.log(
                        f"""
                        Success {resp.status_code} \n
                        for request {method} url {resp.request.url} \n
                        headers {resp.request.headers} \n
                        body {resp.request.body}""",
                    )
                return resp
        else:
            try:
                # TODO update error code check logic
                error_code_in_resp = resp.json().get("error")
            except Exception as err:
                raise Exception(
                    f"Get error code failed in resp {resp.text}",
                ) from err
            else:
                if error_code == error_code_in_resp:
                    self.log(
                        f"Error {error_code} check passed resp {resp.text}",
                    )
                else:
                    if break_on_failure:
                        raise Exception(
                            f"Error {error_code} check failed resp {resp.text}",
                        )
                    else:
                        self.log(
                            f"Error: error {error_code} check failed resp {resp.text}",
                        )

    def close_app(self):
        self.closed = True

    def sleep(self, timeout):
        self.log(f"sleep {timeout} seconds")
        gevent.sleep(timeout)

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
                api_deco = elog_deco(self.log_path)(api)
                try:
                    api_deco(**v) if v else api_deco()
                except Exception as e:
                    self.log(f"Execute api {api} failed")
                    end_time = datetime.now()
                    start_time = self.data.get("start_time")
                    method = self.data.get("method")
                    url = self.data.get("url")
                    path = self.data.get("path")
                    if start_time:
                        duration = end_time - start_time
                        self.log(
                            f"""Time cost
                            {duration.seconds} seconds,
                            {duration.microseconds} microseconds
                            """,
                        )
                        self.performance_result.append(
                            {
                                f"{self.name} {method} {url}{path}": {
                                    "duration": f"""
                                    {duration.seconds}-seconds-
                                    {duration.microseconds // 1000}-milliseconds-
                                    {duration.microseconds % 1000}-microseconds
                                    """,
                                },
                            },
                        )
                    self.api.add(
                        re.sub(r"\d{2,20}", "*", f"{url}{path}", count=10),
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
                    self.close_app()
                    return
                else:
                    self.log(f"api {api} passed")
        self.case.status = "pass"
        self.result.append(self.case)
        tlog(
            f"{threading.current_thread().name} case {self.case.id} {self.case.name} pass",
        )
        self.close_app()
