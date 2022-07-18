from gat.model import Model


class Device(Model):
    def __init__(self, device_info):
        self.device_id: str = device_info["device_id"]
        self.platform_version: str = device_info.get("platform_version")
        self.system_port: str = device_info.get("system_port")
