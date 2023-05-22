// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

public abstract class OpenAIClientBase : ClientBase
{
    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    private protected override OpenAIClient Client { get; }

    /// <summary>
    /// Create an instance of the OpenAI connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="logger">Application logger</param>
    private protected OpenAIClientBase(
        string modelId,
        string apiKey,
        HttpClient httpClient,
        string? organization = null,
        ILogger? logger = null
    )
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        var options = new OpenAIClientOptions();
        //The following three lines turn off the internal AzureOpenAI retry mechanism in order to ensure consistent retry policies across all connectors.
        options.Transport = new HttpClientTransport(httpClient);
        options.RetryPolicy = null;
        options.Retry.MaxRetries = 0;

        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), HttpPipelinePosition.PerCall);
        }

        this.Client = new OpenAIClient(apiKey, options);
    }
}
