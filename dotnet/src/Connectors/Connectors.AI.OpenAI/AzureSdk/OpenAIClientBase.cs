// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

public abstract class OpenAIClientBase : ClientBase
{
    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    protected override OpenAIClient Client { get; }

    /// <summary>
    /// Create an instance of the OpenAI connector
    /// </summary>
    /// <param name="modelId">Model name</param>
    /// <param name="apiKey">OpenAI API Key</param>
    /// <param name="organization">OpenAI Organization Id (usually optional)</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    protected OpenAIClientBase(
        string modelId,
        string apiKey,
        string? organization = null,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null
    )
    {
        Verify.NotEmpty(modelId, "The Model Id cannot be empty");
        this.ModelId = modelId;

        var options = new OpenAIClientOptions();

        // TODO: reimplement
        // Doesn't work
        // if (handlerFactory != null)
        // {
        //     options.Transport = new HttpClientTransport(handlerFactory.Create(log));
        // }

        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), HttpPipelinePosition.PerCall);
        }

        Verify.NotEmpty(apiKey, "The OpenAI API key cannot be empty");
        this.Client = new OpenAIClient(apiKey, options);
    }
}
