// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using KernelHttpServer.Config;
using KernelHttpServer.Utils;
using Microsoft.Azure.Functions.Worker.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

namespace KernelHttpServer;

internal static class SemanticKernelFactory
{
    private const string SKHTTPHeaderModel = "x-ms-sk-model";
    private const string SKHTTPHeaderEndpoint = "x-ms-sk-endpoint";
    private const string SKHTTPHeaderAPIKey = "x-ms-sk-apikey";
    private const string SKHTTPHeaderCompletion = "x-ms-sk-completion-backend";
    private const string SKHTTPHeaderMSGraph = "x-ms-sk-msgraph";

    internal static IKernel? CreateForRequest(HttpRequestData req, ILogger logger, IEnumerable<string>? skillsToLoad = null)
    {
        var apiConfig = new ApiKeyConfig();

        if (req.Headers.TryGetValues(SKHTTPHeaderCompletion, out var service))
        {
            apiConfig.CompletionBackend = Enum.Parse<CompletionService>(service.First());
        }

        if (req.Headers.TryGetValues(SKHTTPHeaderModel, out var modelValues))
        {
            apiConfig.DeploymentOrModelId = modelValues.First();
            apiConfig.Label = apiConfig.DeploymentOrModelId;
        }

        if (req.Headers.TryGetValues(SKHTTPHeaderEndpoint, out var endpointValues))
        {
            apiConfig.Endpoint = endpointValues.First();
        }

        if (req.Headers.TryGetValues(SKHTTPHeaderAPIKey, out var apikeyValues))
        {
            apiConfig.Key = apikeyValues.First();
        }

        if (!apiConfig.IsValid())
        {
            return null;
        }

        var kernel = KernelBuilder.Create();
        kernel.ConfigureCompletionBackend(apiConfig);

        kernel.RegisterSemanticSkills(RepoFiles.SampleSkillsPath(), logger, skillsToLoad);
        kernel.RegisterNativeSkills(skillsToLoad);
        kernel.RegisterPlanner();

        if (req.Headers.TryGetValues(SKHTTPHeaderMSGraph, out var graphToken))
        {
            kernel.RegisterNativeGraphSkills(graphToken.First());
        }

        return kernel;
    }
}
