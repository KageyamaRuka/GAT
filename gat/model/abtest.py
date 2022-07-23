from model import Model


class ABTest(Model):
    def __init__(self, app_info):
        self.platform: str = "ABTest"
        self.driver: str = app_info["driver"]
        self.mitm_host: str = app_info.get("mitm_host")
        self.mitm_port: str = app_info.get("mitm_port")
        self.kafka_host: str = app_info.get("kafka_host")
        self.kafka_port: str = app_info.get("kafka_port")
