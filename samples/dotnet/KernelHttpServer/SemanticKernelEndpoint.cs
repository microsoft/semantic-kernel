// Copyright (c) Microsoft. All rights reserved.
// Licensed under the MIT License.

using System.Linq;
using System.Net;
using System.Text.Json;
using System.Threading.Tasks;
using KernelHttpServer.Model;
using Microsoft.Azure.Functions.Worker;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;

namespace KernelHttpServer;

public class SemanticKernelEndpoint
{
    [Function("InvokeFunction")]
    public async Task<HttpResponseData> InvokeFunctionAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "skills/{skillName}/invoke/{functionName}")]
        HttpRequestData req,
        FunctionContext executionContext, string skillName, string functionName)
    {
        // in this sample we are using a per-request kernel that is created on each invocation
        // once created, we feed the kernel the ask received via POST from the client
        // and attempt to invoke the function with the given name

        var ask = await JsonSerializer.DeserializeAsync<Ask>(req.Body, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

        if (ask == null)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, "Invalid request, unable to parse the request payload");
        }

        var kernel = SemanticKernelFactory.CreateForRequest(
            req,
            executionContext.GetLogger<SemanticKernelEndpoint>(),
            ask.Skills);

        if (kernel == null)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, "Missing one or more expected HTTP Headers");
        }

        var f = kernel.Skills.GetFunction(skillName, functionName);

        var contextVariables = new ContextVariables(ask.Value);

        foreach (var input in ask.Inputs)
        {
            contextVariables.Set(input.Key, input.Value);
        }

        var result = await kernel.RunAsync(contextVariables, f);

        if (result.ErrorOccurred)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, result.LastErrorDescription);
        }

        var r = req.CreateResponse(HttpStatusCode.OK);
        await r.WriteAsJsonAsync(new AskResult { Value = result.Result, State = result.Variables.Select(v => new AskInput { Key = v.Key, Value = v.Value }) });
        return r;
    }

    [Function("ExecutePlan")]
    public async Task<HttpResponseData> ExecutePlanAsync(
        [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "planner/execute/{maxSteps?}")]
        HttpRequestData req,
        FunctionContext executionContext, int? maxSteps = 10)
    {
        var ask = await JsonSerializer.DeserializeAsync<Ask>(req.Body, new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

        if (ask == null)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, "Invalid request, unable to parse the request payload");
        }

        var kernel = SemanticKernelFactory.CreateForRequest(
            req,
            executionContext.GetLogger<SemanticKernelEndpoint>());

        if (kernel == null)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, "Missing one or more expected HTTP Headers");
        }

        var contextVariables = new ContextVariables(ask.Value);

        foreach (var input in ask.Inputs)
        {
            contextVariables.Set(input.Key, input.Value);
        }

        var planner = kernel.Skills.GetFunction("plannerskill", "executeplan");
        var result = await kernel.RunAsync(contextVariables, planner);

        var iterations = 1;

        while (!result.Variables.ToPlan().IsComplete &&
               result.Variables.ToPlan().IsSuccessful &&
               iterations < maxSteps)
        {
            result = await kernel.RunAsync(result.Variables, planner);
            iterations++;
        }

        if (result.ErrorOccurred)
        {
            return await req.CreateResponseWithMessageAsync(HttpStatusCode.BadRequest, result.LastErrorDescription);
        }

        var r = req.CreateResponse(HttpStatusCode.OK);
        await r.WriteAsJsonAsync(new AskResult { Value = result.Variables.ToPlan().Result });
        return r;
    }
}
