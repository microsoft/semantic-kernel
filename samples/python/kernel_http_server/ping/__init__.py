import logging

import azure.functions as func


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("ping request")

    # Returns a 200 OK response
    return func.HttpResponse()
