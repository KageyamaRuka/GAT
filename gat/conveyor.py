import gevent
from functools import partial

from model.task import Task
from utility import elog_deco
from utility import tlog

from gat.app.http.demo import DemoHttp


class Conveyor:
    debug: bool
    task: Task

    def __init__(
        self,
        task: Task,
        mongo: bool,
        redis: bool,
        env: str,
        debug: bool,
    ):
        """
        log: logging method for current thread logging
        driver: Driver class for app in task
        elog_deco: error logging decorator for stack tracing logging when exception raised with current thread info number, Thread created for every device with a case pop from case_pool.
        """
        self.task: Task = task
        self.log = partial(tlog, log_path=task.log_path)

        driver = eval(task.app.driver)

        driver.__init__ = elog_deco(task.log_path)(driver.__init__)

        self.pool = [
            gevent.spawn(
                driver,
                config={
                    **device.__dict__,
                    **task.app.__dict__,
                    "env": env,
                    "mongo": mongo,
                    "redis": redis,
                    "debug": debug,
                },
                task=task,
            )
            for device in task.device
        ]

        gevent.joinall(self.pool)

        for case in task.result:
            if case.status == "failed":
                task.status = "failed"
                break
        else:
            task.status = "pass"
