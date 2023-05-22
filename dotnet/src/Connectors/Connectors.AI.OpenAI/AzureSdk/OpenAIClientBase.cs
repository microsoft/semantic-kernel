// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.Policies;
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
        Verify.NotNull(httpClient);

        var options = new OpenAIClientOptions();
        // The following lines enable the reuse of globally configured SK SDK policies that are configured on the custom HTTPClient.
        options.Transport = new HttpClientTransport(httpClient);
        options.RetryPolicy = new NoRetryPolicy();

        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), HttpPipelinePosition.PerCall);
        }

        this.Client = new OpenAIClient(apiKey, options);
    }
}
