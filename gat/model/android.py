from gat.model import Model


class Android(Model):
    def __init__(self, app_info):
        self.appium_url: str = app_info.get("appium_url")
        self.platform: str = app_info["platform"]
        self.automation_name: str = app_info.get("automation_name")
        self.app_package: str = app_info.get("app")
        self.app_activity: str = app_info.get("app_activity")
        self.driver: str = app_info["driver"]
