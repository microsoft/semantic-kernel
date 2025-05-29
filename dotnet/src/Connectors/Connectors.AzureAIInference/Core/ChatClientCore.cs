// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using Azure;
using Azure.AI.Inference;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Services;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.AzureAIInference.Core;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with Azure AI Inference services.
/// </summary>
internal sealed class ChatClientCore
{
    /// <summary>
    /// Non-default endpoint for Azure AI Inference API.
    /// </summary>
    internal Uri? Endpoint { get; init; }

    /// <summary>
    /// Non-default endpoint for Azure AI Inference API.
    /// </summary>
    internal string? ModelId { get; init; }

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; init; }

    /// <summary>
    /// Azure AI Inference Client
    /// </summary>
    internal ChatCompletionsClient Client { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Optional target Model Id for endpoints that support multiple models</param>
    /// <param name="apiKey">Azure AI Inference API Key.</param>
    /// <param name="endpoint">Azure AI Inference compatible API endpoint.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal ChatClientCore(
        string? modelId = null,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        this.Logger = logger ?? NullLogger.Instance;
        // Accepts the endpoint if provided, otherwise uses the default Azure AI Inference endpoint.
        this.Endpoint = endpoint ?? httpClient?.BaseAddress;
        Verify.NotNull(this.Endpoint, "endpoint or base-address");
        this.AddAttribute(AIServiceExtensions.EndpointKey, this.Endpoint.ToString());

        if (string.IsNullOrEmpty(apiKey))
        {
            // Api Key is not required, when not provided will be set to single space to avoid empty exceptions from Azure SDK AzureKeyCredential type.
            // This is a common scenario when using the Azure AI Inference service thru a Gateway that may inject the API Key.
            apiKey = SingleSpace;
        }

        if (!string.IsNullOrEmpty(modelId))
        {
            this.ModelId = modelId;
            this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        this.Client = new ChatCompletionsClient(this.Endpoint, new AzureKeyCredential(apiKey!), GetClientOptions(httpClient));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Optional target Model Id for endpoints that support multiple models</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="endpoint">Azure AI Inference compatible API endpoint.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal ChatClientCore(
        string? modelId = null,
        TokenCredential? credential = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);
        this.Logger = logger ?? NullLogger.Instance;

        this.Endpoint = endpoint ?? httpClient?.BaseAddress;
        Verify.NotNull(this.Endpoint, "endpoint or base-address");
        this.AddAttribute(AIServiceExtensions.EndpointKey, this.Endpoint.ToString());

        if (!string.IsNullOrEmpty(modelId))
        {
            this.ModelId = modelId;
            this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        this.Client = new ChatCompletionsClient(this.Endpoint, credential, GetClientOptions(httpClient));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatClientCore"/> class using the specified Azure AI Inference Client.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="modelId">Target Model Id for endpoints supporting more than one</param>
    /// <param name="chatClient">Custom <see cref="ChatCompletionsClient"/>.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ChatClientCore(
        string? modelId,
        ChatCompletionsClient chatClient,
        ILogger? logger = null)
    {
        Verify.NotNull(chatClient);
        if (!string.IsNullOrEmpty(modelId))
        {
            this.ModelId = modelId;
            this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        this.Logger = logger ?? NullLogger.Instance;
        this.Client = chatClient;
    }

    /// <summary>
    /// Allows adding attributes to the client.
    /// </summary>
    /// <param name="key">Attribute key.</param>
    /// <param name="value">Attribute value.</param>
    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

    #region Private

    /// <summary>
    /// Single space constant.
    /// </summary>
    private const string SingleSpace = " ";

    /// <summary>Gets options to use for an Azure AI InferenceClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceVersion">Optional API version.</param>
    /// <returns>An instance of <see cref="AzureAIInferenceClientOptions"/>.</returns>
    internal static AzureAIInferenceClientOptions GetClientOptions(HttpClient? httpClient, AzureAIInferenceClientOptions.ServiceVersion? serviceVersion = null)
    {
        AzureAIInferenceClientOptions options = serviceVersion is not null ?
            new(serviceVersion.Value) :
            new();

        options.Diagnostics.ApplicationId = HttpHeaderConstant.Values.UserAgent;

        options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ChatClientCore))), Azure.Core.HttpPipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientTransport(httpClient);
            options.RetryPolicy = new RetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
            options.Retry.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable default timeout
        }

        return options;
    }

    #endregion
}
