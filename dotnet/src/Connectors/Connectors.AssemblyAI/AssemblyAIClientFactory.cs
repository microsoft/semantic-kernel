// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using AssemblyAI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AssemblyAI;

internal static class AssemblyAIClientFactory
{
    public static AssemblyAIClient Create(
        string apiKey,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNullOrWhiteSpace(apiKey);
        return new AssemblyAIClient(new ClientOptions
        {
            ApiKey = apiKey,
            BaseUrl = endpoint?.ToString() ?? AssemblyAIClientEnvironment.Default,
            HttpClient = HttpClientProvider.GetHttpClient(httpClient),
            UserAgent = new UserAgent { ["integration"] = new("SK", "1.0.0") }
        });
    }
}
