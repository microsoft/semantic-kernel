// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure;
using Azure.AI.Inference;
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
internal class ChatClientCore
{
    /// <summary>
    /// Single space constant.
    /// </summary>
    private const string SingleSpace = " ";

    /// <summary>
    /// Identifier of the default model to use
    /// </summary>
    protected internal string ModelId { get; init; } = string.Empty;

    /// <summary>
    /// Non-default endpoint for Azure AI Inference API.
    /// </summary>
    protected internal Uri? Endpoint { get; init; }

    /// <summary>
    /// Logger instance
    /// </summary>
    protected internal ILogger? Logger { get; init; }

    /// <summary>
    /// Azure AI Inference Client
    /// </summary>
    protected internal ChatCompletionsClient? ChatClient { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Model name.</param>
    /// <param name="apiKey">Azure AI Inference API Key.</param>
    /// <param name="endpoint">Azure AI Inference compatible API endpoint.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ChatClientCore(
        string? modelId = null,
        string? apiKey = null,
        Uri? endpoint = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        // Empty constructor will be used when inherited by a specialized Client.
        if (modelId is null
            && apiKey is null
            && endpoint is null
            && httpClient is null
            && logger is null)
        {
            return;
        }

        if (!string.IsNullOrWhiteSpace(modelId))
        {
            this.ModelId = modelId!;
            this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        this.Logger = logger ?? NullLogger.Instance;

        // Accepts the endpoint if provided, otherwise uses the default Azure AI Inference endpoint.
        this.Endpoint = endpoint ?? httpClient?.BaseAddress;
        Verify.NotNull(this.Endpoint);

        if (string.IsNullOrEmpty(apiKey))
        {
            // Avoids an exception from Azure AI Inference Client when a custom endpoint is provided without an API key.
            apiKey = SingleSpace;
        }

        this.AddAttribute(AIServiceExtensions.EndpointKey, this.Endpoint.ToString());

        var options = GetClientOptions(httpClient);

        this.ChatClient = new ChatCompletionsClient(this.Endpoint, new AzureKeyCredential(apiKey!), options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatClientCore"/> class using the specified Azure AI InferenceClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="modelId">Azure AI Inference model Id</param>
    /// <param name="chatClient">Custom <see cref="ChatCompletionsClient"/>.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ChatClientCore(
        string? modelId,
        ChatCompletionsClient chatClient,
        ILogger? logger = null)
    {
        // Model Id may not be required when other services. i.e: File Service.
        if (modelId is not null)
        {
            this.ModelId = modelId;
            this.AddAttribute(AIServiceExtensions.ModelIdKey, modelId);
        }

        Verify.NotNull(chatClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.ChatClient = chatClient;
    }

    /// <summary>
    /// Logs Azure AI Inference action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    internal void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        if (this.Logger!.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation("Action: {Action}. Azure AI Inference Model ID: {ModelId}.", callerMemberName, this.ModelId);
        }
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

    /// <summary>Gets options to use for an Azure AI InferenceClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="serviceVersion">Optional API version.</param>
    /// <returns>An instance of <see cref="ChatCompletionsClientOptions"/>.</returns>
    private static ChatCompletionsClientOptions GetClientOptions(HttpClient? httpClient, ChatCompletionsClientOptions.ServiceVersion? serviceVersion = null)
    {
        ChatCompletionsClientOptions options = serviceVersion is not null ?
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

    /// <summary>
    /// Invokes the specified request and handles exceptions.
    /// </summary>
    /// <typeparam name="T">Type of the response.</typeparam>
    /// <param name="request">Request to invoke.</param>
    /// <returns>Returns the response.</returns>
    protected static async Task<T> RunRequestAsync<T>(Func<Task<T>> request)
    {
        try
        {
            return await request.Invoke().ConfigureAwait(false);
        }
        catch (RequestFailedException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    /// <summary>
    /// Invokes the specified request and handles exceptions.
    /// </summary>
    /// <typeparam name="T">Type of the response.</typeparam>
    /// <param name="request">Request to invoke.</param>
    /// <returns>Returns the response.</returns>
    protected static T RunRequest<T>(Func<T> request)
    {
        try
        {
            return request.Invoke();
        }
        catch (RequestFailedException e)
        {
            throw e.ToHttpOperationException();
        }
    }
}
