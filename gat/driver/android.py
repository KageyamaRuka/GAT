from typing import Dict
from typing import Optional

import uiautomator2
from model.task import Task


class Android:
    def __init__(self, config: Dict, task: Optional[Task]):
        self.config = config
        self.task = task
        self.device_id = config.get("device_id")
        self.device = uiautomator2.connect(self.device_id)
        self.device.app_stop_all()
