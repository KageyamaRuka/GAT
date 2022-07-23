from typing import Any
from typing import List
from typing import Optional
from typing import Union

from model import Model
from model.android import Android
from model.case import Case
from model.device import Device
from model.http import Http
from model.ios import IOS
from model.protobuf import Protobuf
from model.windows import Windows


class Task(Model):
    def __init__(self, task_info: dict[str, Any]):
        self.id: int = task_info["id"]
        self.name: str = task_info["name"]
        self.device: List[Device] = [
            Device(device_info) for device_info in task_info["device"]
        ]
        self.app: Union[Android, IOS, Windows, Protobuf, Http] = eval(
            task_info["app"]["platform"].capitalize(),
        )(task_info["app"])
        self.case: List[Case] = [
            Case(case_info) for case_info in task_info["case"]
        ]
        self.status: str = "init"
        self.log_path: Optional[str] = task_info.get("log_path")
        self.result: List[Case] = []
        # TODO move repeat flag in execution fileds
        self.repeat: Optional[int] = task_info.get("repeat")
        self.pass_rate = 0

    def dictify(self):
        return {
            "id": self.id,
            "name": self.name,
            "device": [device.__dict__ for device in self.device],
            "app": self.app.__dict__,
            "case": [case.__dict__ for case in self.case],
            "status": self.status,
            "log_path": self.log_path,
            "result": [case.__dict__ for case in self.result],
        }

    def __repr__(self):
        return str(self.dictify())
