# fmt: off
from gevent import monkey

monkey.patch_all()  # noreorder pylint: disable=E702
# fmt: on

from utility import yaml_loader
from utility import yaml_dumper
from utility import tprint
from utility import timestamp
from utility import elog_deco
from conveyor import Conveyor
from model.task import Task
from model.device import Device
from typing import List
from copy import deepcopy
import sys
import os
import jinja2
import gevent


class Worker(object):
    debug: bool
    info: bool
    task: Task
    log_path: str
    scheduler: List[gevent.Greenlet]

    def __init__(
        self,
        repeat=None,
        env=None,
        threads=1,
        mongo=True,
        redis=True,
        mode="local",
        debug=False,
    ):
        self.repeat = repeat
        self.env = env
        self.threads = threads
        self.mongo = mongo
        self.redis = redis
        self.mode = mode
        self.debug = debug
        self.tag = timestamp()
        tprint(
            f"Now {mode} worker start working, env info {env}, thread info {threads}, repeat info {repeat}, debug {debug}",
        )
        if mode == "local":
            self.local_execute()

    def local_execute(self):
        self.create_log_dir()
        self.task: Task = self.get_local_task()
        self.task.log_path = self.log_path
        self.task.date = self.tag
        Conveyor.__init__ = elog_deco(self.task.log_path)(
            Conveyor.__init__,
        )
        self.scheduler = [
            gevent.spawn(
                Conveyor,
                self.task,
                self.mongo,
                self.redis,
                self.env,
                self.debug,
            ),
        ]
        gevent.joinall(self.scheduler)
        self.create_report()
        self.analyze_report()

    def analyze_report(self):
        if self.task.pass_rate < 20:
            sys.exit(-1)
        else:
            sys.exit(0)

    def create_report(self):
        report = {}
        passed = 0
        report["case"] = {}
        report["case"]["pass"] = []
        report["case"]["failed"] = []
        for case in self.task.result:
            if case.status == "pass":
                report["case"]["pass"].append(case.name)
                passed += 1
            else:
                report["case"]["failed"].append(
                    {case.name: {"api": case.failed_reason}},
                )
        self.task.total = f"Total: {len(self.task.result)}"
        self.task.passed = f"Passed: {passed}"
        self.task.failed = f"Failed: {len(self.task.result) - passed}"
        self.task.pass_rate = round(passed / len(self.task.result) * 100)
        self.task.failed_rate = 100 - self.task.pass_rate
        with open("report_template.html") as f:
            template = jinja2.Template(f.read())
        with open(f"{self.log_path}/report.html", "w+", encoding="utf-8") as f:
            f.write(template.render(task=self.task))

    def create_log_dir(self):
        if not os.path.exists("log"):
            os.mkdir("log")
        self.log_path = f"log/{self.tag}"
        os.makedirs(self.log_path)
        tprint(f"Log folder {self.log_path} created")

    def get_local_task(self) -> Task:
        """
        Create task dir if not exist.
        Filter *.yaml file with the same app platform and name defined in the first yaml file.(need to update to specific driver name in the future)
        Collect all the *.yaml file in task dir and create a total task.yaml with all cases.
        """
        if not os.path.exists("task"):
            os.mkdir("task")
            raise Exception("Task dir empty, no task file")

        yaml_files: List[str] = os.listdir("task")
        yaml_files = [f for f in yaml_files if f.endswith("yaml")]
        if len(yaml_files) == 0:
            raise Exception("Task dir empty, no task file")
        tprint(f"Get task file {yaml_files}")

        # preload the first task file for filtering later
        task: Task = Task(yaml_loader(f"task/{yaml_files[0]}"))
        task.name = "Daily Regression"

        # TODO move threads info into Task for better remote execution support
        if task.app.platform.lower() == "http":
            task.device = [
                Device({"udid": f"{task.app.platform.lower()}-{i}"})
                for i in range(self.threads)
            ]

        # filter out task files with different platform or driver
        if len(yaml_files) > 1:
            ts: List[Task] = [
                Task(yaml_loader(f"task/{yaml_file}"))
                for yaml_file in yaml_files[1:]
                if Task(yaml_loader(f"task/{yaml_file}")).app.platform
                == task.app.platform
                and Task(yaml_loader(f"task/{yaml_file}")).app.driver
                == task.app.driver
            ]
            [[task.case.append(case) for case in t.case] for t in ts]

        # re-arrange the case id
        for i in range(len(task.case)):
            task.case[i].id = i + 1

        # re-arrange with the repeated cases
        # TODO repeat might need to be migrated into task file in the future
        if self.repeat is not None:
            case_num = len(task.case)
            new_cases = []
            for i in range(1, self.repeat):
                for case in task.case:
                    new_case = deepcopy(case)
                    new_case.id = case.id + case_num * i
                    new_cases.append(new_case)
            task.case += new_cases

        yaml_dumper(task.dictify(), f"{self.log_path}/task.yaml")

        # TODO might need update to send the performance info to remote server directly in the future
        if task.app.platform.lower() == "http":
            yaml_dumper(info=[], file_path=f"{self.log_path}/performance.yaml")
            yaml_dumper(info=[], file_path=f"{self.log_path}/api.yaml")

        return task


if __name__ == "__main__":
    env_info = None
    thread_info = 1
    repeat_info = None
    mongo_info = True
    redis_info = True
    debug_info = False
    for arg in sys.argv:
        if "env" in arg:
            env_info = arg.replace("env=", "")
        if "threads" in arg:
            thread_info = int(arg.replace("threads=", ""))
        if "repeat" in arg:
            repeat_info = int(arg.replace("repeat=", ""))
        if "mongo" in arg:
            mongo_info = (
                False if arg.replace("mongo=", "").lower() == "false" else True
            )
        if "redis" in arg:
            redis_info = (
                False if arg.replace("redis=", "").lower() == "false" else True
            )
        if "debug" in arg:
            debug_info = (
                True if arg.replace("debug=", "").lower() == "true" else False
            )
    Worker(
        repeat=repeat_info,
        env=env_info,
        threads=thread_info,
        mongo=mongo_info,
        redis=redis_info,
        debug=debug_info,
    )
