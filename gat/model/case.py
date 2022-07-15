from typing import Any
from typing import Dict
from typing import List

from gat.model import Model


class Case(Model):
    def __init__(self, case_info):
        self.id: int = case_info["id"]
        self.name: str = case_info["name"]
        self.operations: List[Dict[str, Any]] = case_info["operations"]
        self.status: str = "init"
        self.failed_reason = None
