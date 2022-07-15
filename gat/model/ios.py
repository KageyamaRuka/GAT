from gat.model import Model


class IOS(Model):
    def __init__(self, app_info):
        self.appium_url: str = app_info.get("appium_url")
        self.platform: str = app_info["platform"]
        self.automation_name: str = app_info.get("automation_name")
        self.xcode_signing_id: str = app_info.get("xcode_signing_id")
        self.xcode_org_id: str = app_info.get("xcode_org_id")
        self.bundle_id: str = app_info.get("app")
        self.driver: str = app_info["driver"]
