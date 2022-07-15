from gat.model import Model


class Http(Model):
    def __init__(self, app_info):
        self.driver: str = app_info["driver"]
        self.platform: str = app_info["platform"]
        self.env: str = app_info["env"]
