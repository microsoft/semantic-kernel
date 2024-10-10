// Copyright (c) Microsoft. All rights reserved.

using System.Net;
using System.Reflection;
using System.Text.Json;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace Plugins.AzureFunctions.Extensions;

public class AIPluginRunner
{
    private readonly ILogger<AIPluginRunner> _logger;
    private readonly Kernel _kernel;

    public AIPluginRunner(Kernel kernel, ILoggerFactory loggerFactory)
    {
        this._kernel = kernel;
        this._logger = loggerFactory.CreateLogger<AIPluginRunner>();
    }

    /// <summary>
    /// Runs a prompt using the operationID and returns back an HTTP response.
    /// </summary>
    /// <param name="req"></param>
    /// <param name="pluginName"></param>
    /// <param name="functionName"></param>
    public async Task<HttpResponseData> RunAIPluginOperationAsync<T>(HttpRequestData req, string pluginName, string functionName)
    {
        KernelArguments arguments = ConvertToKernelArguments((await JsonSerializer.DeserializeAsync<T>(req.Body).ConfigureAwait(true))!);

        var response = req.CreateResponse(HttpStatusCode.OK);
        response.Headers.Add("Content-Type", "text/plain;charset=utf-8");
        await response.WriteStringAsync(
            (await this._kernel.InvokeAsync(pluginName, functionName, arguments).ConfigureAwait(false)).ToString()
        ).ConfigureAwait(false);
        return response;
    }

    // Method to convert model to dictionary
    private static KernelArguments ConvertToKernelArguments<T>(T model)
    {
        {
            var arguments = new KernelArguments();
            foreach (PropertyInfo property in typeof(T).GetProperties())
            {
                if (property.GetValue(model) != null)
                {
                    arguments.Add(property.Name, property.GetValue(model));
                }
            }
            return arguments;
        }
    }
}
