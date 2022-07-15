from gat.model import Model


class Windows(Model):
    def __init__(self, app_info):
        self.platform: str = app_info["platform"]
        self.appium_url: str = app_info.get("appium_url")
        self.driver: str = app_info["driver"]
