// Copyright (c) Microsoft. All rights reserved.

/* 
Phase 01 : This class was created adapting and merging ClientCore and OpenAIClientCore classes.
System.ClientModel changes were added and adapted to the code as this package is now used as a dependency over OpenAI package.
All logic from original ClientCore and OpenAIClientCore were preserved.
*/

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Net.Http;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using OpenAI;
using OpenAI.Embeddings;

#pragma warning disable CA2208 // Instantiate argument exceptions correctly

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal class ClientCore
{
    /// <summary>
    /// Model Id
    /// </summary>
    internal string ModelId { get; set; } = string.Empty;

    /// <summary>
    /// Non-default endpoint for OpenAI API.
    /// </summary>
    internal Uri? Endpoint { get; set; } = null;

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; set; }

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal OpenAIClient Client { get; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Model name.</param>
    /// <param name="apiKey">OpenAI API Key.</param>
    /// <param name="endpoint">OpenAI compatible API endpoint.</param>
    /// <param name="organization">OpenAI Organization Id (usually optional).</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this.Logger = logger ?? NullLogger.Instance;
        this.ModelId = modelId;

        // Accepts the endpoint if provided, otherwise uses the default OpenAI endpoint.
        this.Endpoint = endpoint ?? httpClient?.BaseAddress;
        if (this.Endpoint is null)
        {
            Verify.NotNullOrWhiteSpace(apiKey); // For Public OpenAI Endpoint a key must be provided.
        }

        var options = GetOpenAIClientOptions(httpClient, this.Endpoint);
        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), PipelinePosition.PerCall);
        }

        this.Client = new OpenAIClient(apiKey ?? string.Empty, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientCore"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string modelId,
        OpenAIClient openAIClient,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.ModelId = modelId;
        this.Client = openAIClient;
    }

    /// <summary>
    /// Logs OpenAI action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    internal void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation("Action: {Action}. OpenAI Model ID: {ModelId}.", callerMemberName, this.ModelId);
        }
    }

    /// <summary>
    /// Generates an embedding from the given <paramref name="data"/>.
    /// </summary>
    /// <param name="data">List of strings to generate embeddings for</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="dimensions">The number of dimensions the resulting output embeddings should have. Only supported in "text-embedding-3" and later models.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>List of embeddings</returns>
    internal async Task<IList<ReadOnlyMemory<float>>> GetEmbeddingsAsync(
        IList<string> data,
        Kernel? kernel,
        int? dimensions,
        CancellationToken cancellationToken)
    {
        var result = new List<ReadOnlyMemory<float>>(data.Count);

        if (data.Count > 0)
        {
            var embeddingsOptions = new EmbeddingGenerationOptions()
            {
                Dimensions = dimensions
            };

            ClientResult<EmbeddingCollection> response = await RunRequestAsync(() => this.Client.GetEmbeddingClient(this.ModelId).GenerateEmbeddingsAsync(data, embeddingsOptions, cancellationToken)).ConfigureAwait(false);
            var embeddings = response.Value;

            if (embeddings.Count != data.Count)
            {
                throw new KernelException($"Expected {data.Count} text embedding(s), but received {embeddings.Count}");
            }

            for (var i = 0; i < embeddings.Count; i++)
            {
                result.Add(embeddings[i].Vector);
            }
        }

        return result;
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

    /// <summary>Gets options to use for an OpenAIClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="endpoint">Endpoint for the OpenAI API.</param>
    /// <returns>An instance of <see cref="OpenAIClientOptions"/>.</returns>
    private static OpenAIClientOptions GetOpenAIClientOptions(HttpClient? httpClient, Uri? endpoint)
    {
        // As the options Endpoint is an init property and I can't set it afterwards,
        // I need an if statement to create the options for a custom endpoint.
        OpenAIClientOptions options = (endpoint is null)
            ? new OpenAIClientOptions() { ApplicationId = HttpHeaderConstant.Values.UserAgent }
            : new OpenAIClientOptions() { ApplicationId = HttpHeaderConstant.Values.UserAgent, Endpoint = endpoint };

        options.AddPolicy(new AddHeaderRequestPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore))), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable default timeout
        }

        return options;
    }

    /// <summary>
    /// Invokes the specified request and handles exceptions.
    /// </summary>
    /// <typeparam name="T">Type of the response.</typeparam>
    /// <param name="request">Request to invoke.</param>
    /// <returns>Returns the response.</returns>
    private static async Task<T> RunRequestAsync<T>(Func<Task<T>> request)
    {
        try
        {
            return await request.Invoke().ConfigureAwait(false);
        }
        catch (ClientResultException e)
        {
            throw e.ToHttpOperationException();
        }
    }
}
