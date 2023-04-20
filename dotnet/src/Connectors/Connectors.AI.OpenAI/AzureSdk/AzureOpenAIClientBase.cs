// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Reliability;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

public abstract class AzureOpenAIClientBase : ClientBase
{
    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    protected override OpenAIClient Client { get; }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance using API Key auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    protected AzureOpenAIClientBase(
        string modelId,
        string endpoint,
        string apiKey,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null)
    {
        Verify.NotEmpty(modelId, "The Model Id/Deployment Name cannot be empty");
        this.ModelId = modelId;

        var options = new OpenAIClientOptions();

        // TODO: reimplement
        // Doesn't work
        // if (handlerFactory != null)
        // {
        //     options.Transport = new HttpClientTransport(handlerFactory.Create(log));
        // }

        Verify.NotEmpty(endpoint, "The Azure endpoint cannot be empty");
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        Verify.NotEmpty(apiKey, "The Azure API key cannot be empty");
        this.Client = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(apiKey), options);
    }

    /// <summary>
    /// Creates a new AzureTextCompletion client instance supporting AAD auth
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credentials">Token credentials, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="handlerFactory">Retry handler factory for HTTP requests.</param>
    /// <param name="log">Application logger</param>
    protected AzureOpenAIClientBase(
        string modelId,
        string endpoint,
        TokenCredential credentials,
        IDelegatingHandlerFactory? handlerFactory = null,
        ILogger? log = null)
    {
        Verify.NotEmpty(modelId, "The Model Id/Deployment Name cannot be empty");
        this.ModelId = modelId;

        var options = new OpenAIClientOptions();

        // TODO: reimplement
        // Doesn't work
        // if (handlerFactory != null)
        // {
        //     options.Transport = new HttpClientTransport(handlerFactory.Create(log));
        // }

        Verify.NotEmpty(endpoint, "The Azure endpoint cannot be empty");
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        this.Client = new OpenAIClient(new Uri(endpoint), credentials, options);
    }
}
