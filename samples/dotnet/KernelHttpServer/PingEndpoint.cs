// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;

// This endpoint exists as a convenience for the UI to check if the function it is dependent
// on is running. You won't need this endpoint in a typical app.
namespace KernelHttpServer;

public class PingEndpoint
{
    [Function("Ping")]
    public HttpResponseData Ping(
        [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "ping")]
        HttpRequestData req,
        FunctionContext executionContext)
    {
        return req.CreateResponse(HttpStatusCode.OK);
    }
}
