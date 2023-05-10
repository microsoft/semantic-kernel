import azure.functions as func

from utils.kernel_server import KernelServer


async def main(req: func.HttpRequest) -> func.HttpResponse:
    kernel_server = KernelServer()
    return await kernel_server.completion(req)
