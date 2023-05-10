import azure.functions as func

from utils.kernel_server import KernelServer


async def main(req: func.HttpRequest) -> func.HttpResponse:
    kernel_server = KernelServer()
    max_steps = req.params.get("maxsteps")
    return await kernel_server.execute_plan(req, max_steps)
