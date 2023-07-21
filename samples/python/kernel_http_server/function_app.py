import azure.functions as func
import logging

from utils.kernel_server import KernelServer

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="skills/{skillName}/invoke/{functionName}", methods=["POST"])
async def completion(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Completion request")
    kernel_server = KernelServer()
    return await kernel_server.completion(req)


@app.route(route="ping", methods=["GET"])
async def ping(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("ping request")
    return func.HttpResponse()


@app.route(route="planner/createplan", methods=["POST"])
async def create_plan(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Create Plan Request")
    kernel_server = KernelServer()
    return await kernel_server.create_plan(req)


@app.route(route="planner/execute/{maxSteps}", methods=["POST"])
async def execute_plan(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Execute Plan Request")
    kernel_server = KernelServer()
    return await kernel_server.execute_plan(req, req.route_params.get("maxSteps"))
