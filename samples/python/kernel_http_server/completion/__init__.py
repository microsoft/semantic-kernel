import logging
import json

import azure.functions as func
from semantic_kernel import ContextVariables
from semantic_kernel.memory import VolatileMemoryStore

from completion.kernel_utils import create_kernel_for_request
from completion.ask import Ask


class KernelServer:
    def __init__(self):
        self._memory_story = VolatileMemoryStore()

    async def __call__(self, req: func.HttpRequest) -> func.HttpResponse:
        logging.info("Python HTTP trigger function processed a request.")
        logging.info(req)

        ask_data = json.loads(req.get_body())
        ask = Ask(**ask_data)
        logging.info("Ask object: %s", ask)

        skill_name = req.route_params.get("skillName")
        function_name = req.route_params.get("functionName")

        logging.info("skill_name: %s", skill_name)
        logging.info("function_name: %s", function_name)

        kernel = create_kernel_for_request(req, ask.skills, None)

        sk_func = kernel.skills.get_function(skill_name, function_name)
        context_var = ContextVariables(ask.value)

        for ask_input in ask.inputs:
            context_var.set(ask_input["key"], ask_input["value"])

        result = await sk_func.invoke_with_vars_async(input=context_var)

        response = {"value": result.result}
        return func.HttpResponse(body=json.dumps(response), mimetype="application/json")


kernel_server = KernelServer()


async def main(req: func.HttpRequest) -> func.HttpResponse:
    return await kernel_server(req)
