import json
import time
import requests
from ..core import ComponentBase
import lazyllm
from lazyllm import launchers, flows
import random


class LazyLLMDeployBase(ComponentBase):

    def __init__(self, *, launcher=launchers.remote()):
        super().__init__(launcher=launcher)


class DummyDeploy(LazyLLMDeployBase, flows.Pipeline):
    input_key_name = 'inputs'
    default_headers = {'Content-Type': 'application/json'}
    message_format = {
        input_key_name: '',
        'parameters': {
            'do_sample': False,
            'temperature': 0.1,
        }
    }
    
    def __init__(self, launcher=launchers.remote(sync=False), *, stream=False, **kw):
    # def __init__(self, launcher=launchers.empty(sync=False), *, stream=False, **kw):
        super().__init__(launcher=launcher)
        def func():
            def impl(x):
                print(f'input is {x["inputs"]}, parameters is {x["parameters"]}')
                return f'reply for {x["inputs"]}, and parameters is {x["parameters"]}'
            def impl_stream(x):
                for i in range(10):
                    yield f'reply-{i} for {x["inputs"]}, and parameters is {x["parameters"]}\n'
                    time.sleep(0.2)
            return impl_stream if stream else impl
        flows.Pipeline.__init__(self, func,
            deploy.RelayServer(port=random.randint(30000, 40000), launcher=launcher))

    def __call__(self, *args):
        url = flows.Pipeline.__call__(self)
        print(f'dummy deploy url is : {url}')
        return url

    def __repr__(self):
        return flows.Pipeline.__repr__(self)


def verify_fastapi_func(job):
    while True:
        line = job.queue.get()
        if line.startswith('ERROR:'):
            print("Capture error message: ", line, "\n\n")
            return False
        elif 'Uvicorn running on' in line:
            print("Capture startup message:   ",line)
            break
        if job.status == lazyllm.launchers.status.Failed:
            print("Service Startup Failed.")
            return False
    return True
