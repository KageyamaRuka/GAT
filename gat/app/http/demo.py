from gat.driver.http import HttpDriver


class DemoHttp(HttpDriver):
    def __int__(self, config, task):
        super().__init__(config, task)

    def demo(self, code):
        self.log(f"success with {code}")

    def demo_failed(self, code):
        raise Exception(f"failed with {code}")

    def demo_sleep(self, timeout):
        self.sleep(timeout)
