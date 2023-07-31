// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Models;

namespace Extensions;

public class AIPluginRunner : IAIPluginRunner
{
    private readonly ILogger<AIPluginRunner> _logger;
    private readonly IKernel _kernel;

    public AIPluginRunner(IKernel kernel, ILoggerFactory loggerFactory)
    {
        this._kernel = kernel;
        this._logger = loggerFactory.CreateLogger<AIPluginRunner>();
    }

    /// <summary>
    /// Runs a semantic function using the operationID and returns back an HTTP response.
    /// </summary>
    /// <param name="req"></param>
    /// <param name="operationId"></param>
    public async Task<HttpResponseData> RunAIPluginOperationAsync(HttpRequestData req, string operationId)
    {
        try
        {
            ContextVariables contextVariables = LoadContextVariablesFromRequest(req);

            var appSettings = AppSettings.LoadSettings();

            if (!this._kernel.Skills.TryGetFunction(
                skillName: appSettings.AIPlugin.NameForModel,
                functionName: operationId,
                out ISKFunction? function))
            {
                HttpResponseData errorResponse = req.CreateResponse(HttpStatusCode.NotFound);
                await errorResponse.WriteStringAsync($"Function {operationId} not found").ConfigureAwait(false);
                return errorResponse;
            }

            var result = await this._kernel.RunAsync(contextVariables, function).ConfigureAwait(false);

            var response = req.CreateResponse(HttpStatusCode.OK);
            response.Headers.Add("Content-Type", "text/plain;charset=utf-8");
            await response.WriteStringAsync(result.Result).ConfigureAwait(false);
            return response;
        }
#pragma warning disable CA1031
        catch (System.Exception ex)
#pragma warning restore CA1031
        {
            HttpResponseData errorResponse = req.CreateResponse(HttpStatusCode.BadRequest);
            await errorResponse.WriteStringAsync(ex.Message).ConfigureAwait(false);
            return errorResponse;
        }
    }

    /// <summary>
    /// Grabs the context variables to send to the semantic function from the original HTTP request.
    /// </summary>
    /// <param name="req"></param>
    protected static ContextVariables LoadContextVariablesFromRequest(HttpRequestData req)
    {
        if (req is null)
        {
            throw new System.ArgumentNullException(nameof(req));
        }

        ContextVariables contextVariables = new();
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
            string? body = req.ReadAsString();
            if (!string.IsNullOrEmpty(body))
            {
                contextVariables.Update(body);
            }
        }

        return contextVariables;
    }
}
