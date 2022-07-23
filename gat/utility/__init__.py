import imp
import json
import random
import threading
import time
import traceback
from functools import partial

import yaml


def yaml_loader(file_path: str, encoding="utf-8"):
    with open(file_path, encoding=encoding) as f:
        return yaml.load(f, Loader=yaml.FullLoader)


def yaml_dumper(
    info,
    file_path: str,
    mode: str = "w+",
    encoding: str = "utf-8",
):
    with open(file_path, mode=mode, encoding=encoding) as f:
        yaml.dump(info, f, allow_unicode=True)


def json_loader(file_path: str, encoding="utf-8"):
    with open(file_path, encoding=encoding) as f:
        return json.loads(f.read())


def file_reader(file_path: str, encoding="utf-8") -> str:
    with open(file_path, encoding=encoding) as f:
        return f.read()


def file_writer(
    file_path: str,
    data: str,
    mode: str = "w+",
    encoding: str = "utf-8",
):
    with open(file_path, mode=mode, encoding=encoding) as f:
        f.write(str(data))


def tprint(*args, **kwargs):
    prefix: str = f"{timestamp()} {threading.current_thread().name}"
    print(prefix, *args, **kwargs)


def tlog(*args, log_name=None, log_path=None, prefix=None, **kwargs):
    log_file = (
        f"{threading.current_thread().name}.log"
        if log_name is None
        else f"{log_name}.log"
    )
    prefix = timestamp() if prefix is None else prefix
    if log_path:
        log_file = "/".join([log_path, log_file])
        with open(log_file, "a", encoding="utf-8") as f:
            print(prefix, *args, file=f, **kwargs)
    else:
        print(prefix, *args, **kwargs)


def elog_deco(log_path, exception=True):
    def wrapper(f):
        def real_wrapper(*args, **kwargs):
            log = partial(tlog, log_path=log_path)
            try:
                result = f(*args, **kwargs)
            except Exception as e:
                log(traceback.format_exc())
                if exception:
                    raise e
            else:
                return result

        return real_wrapper

    return wrapper


def timestamp(f="%m-%d_%H-%M-%S") -> str:
    value = time.localtime(int(time.time()))
    return time.strftime(f, value)


def random_int(length) -> int:
    return random.randint(int("1" + "0" * (length - 1)), int("9" * length))


def get_index(step=False) -> str:
    file = yaml_loader("index.yaml")
    i = file["index"]
    if step:
        i += 1
    yaml_dumper(info={"index": i}, file_path="index.yaml")
    return str(i)
