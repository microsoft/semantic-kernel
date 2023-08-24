import logging
import json

import azure.functions as func
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel import ContextVariables
from semantic_kernel.memory import VolatileMemoryStore
from semantic_kernel.planning.basic_planner import BasicPlanner
from semantic_kernel.planning.plan import Plan
from utils.kernel_utils import create_kernel_for_request
from utils.ask import Ask, AskResult, AskInput


class GeneratedPlan:
    def __init__(self, result: str):
        self.result = result


class KernelServer:
    _memory_store = VolatileMemoryStore()

    async def completion(self, req: func.HttpRequest) -> func.HttpResponse:
        logging.info("Python HTTP trigger function processed a request.")

        skill_name = req.route_params.get("skillName")
        function_name = req.route_params.get("functionName")

        if not skill_name or not function_name:
            logging.error(
                f"Skill name: {skill_name} or function name: {function_name} not given"
            )
            return func.HttpResponse(
                "Please pass skill_name and function_name on the URL", status_code=400
            )

        logging.info("skill_name: %s", skill_name)
        logging.info("function_name: %s", function_name)

        req_body = {}
        try:
            req_body = req.get_json()
        except ValueError:
            logging.warning("No JSON body provided in request.")
        ask = Ask(**req_body)
        logging.info("Ask object: %s", ask)

        kernel, error_response = create_kernel_for_request(req, [skill_name])
        if error_response:
            return error_response
        try:
            sk_func = kernel.skills.get_function(skill_name, function_name)
        except KernelException:
            logging.exception(
                f"Could not find function {function_name} in skill {skill_name}"
            )
            return func.HttpResponse(
                f"Could not find function {function_name} in skill {skill_name}",
                status_code=404,
            )

        context_var = ContextVariables(ask.value)

        for ask_input in ask.inputs:
            context_var.set(ask_input["key"], ask_input["value"])

        result = await sk_func.invoke_async(variables=context_var)

        if result.error_occurred:
            logging.error("Error occurred: %s", result.last_error_description)
            return func.HttpResponse(
                body=json.dumps({"error": result.last_error_description}),
                mimetype="application/json",
                status_code=500,
            )

        states = [
            AskInput(key=k, value=v) for k, v in result.variables.variables.items()
        ]
        response = AskResult(value=result.result, state=states)
        return func.HttpResponse(body=response.to_json(), mimetype="application/json")

    async def create_plan(self, req: func.HttpRequest):
        logging.info("planner request")
        try:
            planner_data = req.get_json()
        except ValueError:
            logging.warning("No JSON body provided in request.")
            return func.HttpResponse(
                "No JSON body provided in request", status_code=400
            )
        if "skills" not in planner_data or "value" not in planner_data:
            logging.warning("Skills or Value not provided in request.")
            return func.HttpResponse(
                "Skills or Value not provided in request", status_code=400
            )

        skills = planner_data["skills"]
        value = planner_data["value"]

        kernel, error_response = create_kernel_for_request(req, skills)
        if error_response:
            return error_response
        planner = BasicPlanner()
        original_plan = await planner.create_plan_async(value, kernel)
        generated_plan = json.loads(original_plan.generated_plan.result)
        generated_plan["goal"] = original_plan.goal
        generated_plan["prompt"] = original_plan.prompt
        response = {"state": [generated_plan]}
        logging.info("response: %s", original_plan.generated_plan.result)

        states = [AskInput(key=k, value=v) for k, v in generated_plan.items()]
        response = AskResult(value=original_plan.goal, state=states)
        logging.info("response: %s", response.to_json())
        return func.HttpResponse(body=response.to_json(), mimetype="application/json")

    async def execute_plan(self, req: func.HttpRequest, max_steps: int):
        logging.info("planner request")
        planner_data = json.loads(req.get_body())

        if "inputs" not in planner_data:
            logging.warning("Inputs not provided in request.")
            return func.HttpResponse("Inputs not provided in request", status_code=400)

        data_inputs = planner_data["inputs"]

        subtasks = []
        goal = None
        prompt = None

        for data in data_inputs:
            if data["key"] == "goal":
                goal = data["value"]
            elif data["key"] == "prompt":
                prompt = data["value"]
            elif data["key"] == "subtasks":
                subtasks = data["value"]

        # Converting int args to string
        for subtask in subtasks:
            args = subtask.get("args", None)
            if args:
                args = {k: str(v) for k, v in args.items()}
                subtask["args"] = args

        plan_dict = {"input": goal, "prompt": prompt, "subtasks": subtasks}
        generated_plan = GeneratedPlan(json.dumps(plan_dict))
        plan = Plan(goal=goal, prompt=prompt, plan=generated_plan)

        kernel, error_response = create_kernel_for_request(req, None)
        if error_response:
            return error_response

        planner = BasicPlanner()

        result = await planner.execute_plan_async(plan, kernel)

        response = {"value": result}
        logging.info("response: %s", response)
        return func.HttpResponse(body=json.dumps(response), mimetype="application/json")
