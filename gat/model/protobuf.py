from gat.model import Model


class Protobuf(Model):
    def __init__(self, app_info):
        self.driver: str = app_info["driver"]
        self.platform: str = app_info["platform"]
        self.connection: str = app_info["connection"]
