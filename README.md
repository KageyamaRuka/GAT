# GAT
GAT means Generic Automation Toolkit, it can be used in intergration test stage for different scenarios, like UI test for mobile, desktop, and web platforms, API test for http, rpc and other protocols, and firmware test for console devices.

GAT start running with an `Worker` instance which accept several arguments, like `env` for environment info, `threads` for parallel execution info, `repeat` for repeatly execution info and some other optional arguments for different usage.
For now, its has local execution mode only, which means it needs test cases with it to run, the test cases will be defined in `*.yaml` task files, placed in the `task` directory. There is a plan to support remote execution mode in the future that the task info was distributed by the test server which collect test cases from database and save the test result and performance info after execution.

The `Worker` will create a log directory with a timestamp name in `task/log` and the task directory if not exist and then exit with a warning info for the absence of case file, otherwise it will collect all the yaml files and create a new `task.yaml` with all the cases in it. After these steps, the Worker will trigger the `Conveyor` for task execution.

The `Conveyor` will get the task and env info, it will find the exact `Driver` defined in task, initialize it with one thread for each device.

The `Driver` should be implemented for different scenarios, like UI or http mentioned above. There is a base driver embeded in the framework with some basic method, like `logging` and execution strategy. In the future the execution strategy might need to be abstract away from the base driver as an standalone `Executor` class to support different scenarios, like random, repeat or priority. For now, it just support sequential and repeatly execution.

For intergration test, it will need a `Driver` that inherit the base driver and implement methods as `Keywords` for different test steps, like sign_in for http API test, those keywords should always imply a logic step with default or optional arguments for better abstraction.

Here is an example about the execution, an `DemoDriver` will be initialized by the `Conveyor`, get the `Task` and run the cases in the task, for the test cases, there will be several operations defined with keyword and arguments. The driver will execute all the operations for each case, find the method match the operation's keyword in itself, execute it with the arguments defined. If the operation failed, the driver will catch the exception, save the stack tracing info for the api, and mark the case as failed, otherwise it will continue with the next operation until finished and mark the case as pass. After all case finished, the task will be set with pass or failed status based on whether all cases pass or not.

During the whole period, the execution info will be saved into the log file within the log directory. Multiple log files will be generated if `threads` arguments are set, and all the working threads will complete the task cooperatively.

The Worker will analyze the execution info of all the cases, get the passed and failed case number and the pass rate of the task, then it will render a test report using the Jinja report template. If this was runned on Jenkins, we can use the email extension to send out report.

For the toolchain part, we use `pyenv` for python version management and `PDM` as the package manager, `PDM` is a modern package and dependency manager which support PEP 582, it can add/update/remove the dependencies easily.

We also use `pre-commit` hooks for local side checking before we commit the code. There are several hooks in the `.pre-commit-config` yaml file, like `black` as the formatter, `flake8` as style checker for PEP8, `mypy` as static type checker, imports reorder and formatter for both documents and yaml file. When we create a commit, the git hook will trigger the pre-commit extensions, check the source file involed, format the files if possible and prompt the errors in the command line if failed, then we should deal with the errors, clear them before another try, in the end, we will commit the code successfully and push it to the remote repository, sometimes there will be server side format/style/type checker as the CI process, the local side will help us to figure out the errors earlier and pass the server side check easily.
