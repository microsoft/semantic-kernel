// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Threading.Tasks;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;

namespace AIPlugins.AzureFunctions.Extensions;

public class KernelAIPluginRunner : IAIPluginRunner
{
    private const string DefaultSemanticSkillsFolder = "skills";

    private readonly ILogger<KernelAIPluginRunner> _logger;
    private IKernelFactory _kernelFactory;

    public KernelAIPluginRunner(IKernelFactory kernelFactory, ILoggerFactory loggerFactory)
    {
        this._kernelFactory = kernelFactory;
        this._logger = loggerFactory.CreateLogger<KernelAIPluginRunner>();
    }

    public async Task<HttpResponseData> RunAIPluginOperationAsync(HttpRequestData req, string operationId)
    {
        ContextVariables contextVariables = LoadContextVariablesFromRequest(req);

        // Assuming operation ID is of the format "skill/function"
        string[] parts = operationId.Split('/');

        IKernel kernel = this._kernelFactory.CreateKernel();

        var function = kernel.Skills.GetSemanticFunction(parts[0], parts[1]);
        if (function == null)
        {
            HttpResponseData errorResponse = req.CreateResponse(HttpStatusCode.NotFound);
            await errorResponse.WriteStringAsync($"Function {operationId} not found");
            return errorResponse;
        }

        var result = await kernel.RunAsync(contextVariables, function);
        if (result.ErrorOccurred)
        {
            HttpResponseData errorResponse = req.CreateResponse(HttpStatusCode.BadRequest);
            await errorResponse.WriteStringAsync(result.LastErrorDescription);
            return errorResponse;
        }

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "text/plain;charset=utf-8");
        await response.WriteStringAsync(result.Result);
        return response;
    }

    protected static ContextVariables LoadContextVariablesFromRequest(HttpRequestData req)
    {
        ContextVariables contextVariables = new ContextVariables();
        foreach (string? key in req.Query.AllKeys)
        {
            if (!string.IsNullOrEmpty(key))
            {
                contextVariables.Set(key, req.Query[key]);
            }
        }

        // If "input" was not specified in the query string, then check the body
        if (string.IsNullOrEmpty(req.Query.Get("input")))
        {
            // Load the input from the body
            string? body = req.Body.ToString();
            if (!string.IsNullOrEmpty(body))
            {
                contextVariables.Update(body);
            }
        }

        return contextVariables;
    }
}
