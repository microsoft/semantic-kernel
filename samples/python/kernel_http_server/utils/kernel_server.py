import logging
import json

import azure.functions as func
from semantic_kernel import ContextVariables, SKContext
from semantic_kernel.memory import VolatileMemoryStore
from semantic_kernel.planning.basic_planner import BasicPlanner
from semantic_kernel.planning.plan import Plan
from utils.kernel_utils import create_kernel_for_request
from utils.ask import Ask


class GeneratedPlan:
    def __init__(self, result: str):
        self.result = result


class KernelServer:
    _memory_store = VolatileMemoryStore()

    async def completion(self, req: func.HttpRequest) -> func.HttpResponse:
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

        result = await sk_func.invoke_async(variables=context_var)

        if result.error_occurred:
            logging.error("Error occurred: %s", result.error)
            return func.HttpResponse(
                body=json.dumps({"error": result.error}), mimetype="application/json", status_code=500
            )

        response = {"value": result.result}
        return func.HttpResponse(body=json.dumps(response), mimetype="application/json")

    async def create_plan(self, req: func.HttpRequest):
        logging.info("planner request")
        planner_data = json.loads(req.get_body())

        skills = planner_data["skills"]

        value = planner_data["value"]

        kernel = create_kernel_for_request(req, skills, None)
        planner = BasicPlanner()
        original_plan = await planner.create_plan_async(value, kernel)
        generated_plan = json.loads(original_plan.generated_plan.result)
        generated_plan["goal"] = original_plan.goal
        generated_plan["prompt"] = original_plan.prompt
        response = {"state": [generated_plan]}
        logging.info("response: %s", original_plan.generated_plan.result)
        return func.HttpResponse(body=json.dumps(response), mimetype="application/json")

    async def execute_plan(self, req: func.HttpRequest, max_steps: int):
        logging.info("planner request")
        planner_data = json.loads(req.get_body())
        data = planner_data["inputs"][0]

        goal = data["goal"]
        prompt = data["prompt"]
        data["input"] = goal

        for subtask in data["subtasks"]:
            args = subtask.get("args", None)
            if args:
                args = {k: str(v) for k, v in args.items()}
                subtask["args"] = args

        generated_plan = GeneratedPlan(json.dumps(data))
        plan = Plan(goal=goal, prompt=prompt, plan=generated_plan)

        kernel = create_kernel_for_request(req, None, None)
        planner = BasicPlanner()

        result = await planner.execute_plan_async(plan, kernel)
        response = {"value": result}
        logging.info("response: %s", result)
        return func.HttpResponse(body=json.dumps(response), mimetype="application/json")
