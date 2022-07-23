from datetime import datetime
from typing import Dict
from typing import Optional

import requests
from driver import Executor
from model.task import Task


class HttpDriver(Executor):
    def __init__(self, config: Dict, task: Optional[Task]):
        self.debug = config.get("debug", False)
        self.headers: dict[str, str] = {}
        self.name = config.get("device_id")
        self.index = int(self.name.split("-")[-1])
        self.task = task
        self.config = config
        super().__init__()
        self.log(f"Thread {self.name} Config get {config}")
        self.session = requests.Session()
        self.session.trust_env = False
        self.sequential()

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
        self.data["request_start_time"] = datetime.now()
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
        duration = datetime.now() - self.data["request_start_time"]
        self.log(
            f"""Time cost
            {duration.seconds} seconds,
            {duration.microseconds} microseconds
            """,
        )

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
