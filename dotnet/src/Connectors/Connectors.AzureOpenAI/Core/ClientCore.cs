// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Http;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Base class for AI clients that provides common functionality for interacting with OpenAI services.
/// </summary>
internal partial class ClientCore
{
    /// <summary>
    /// Gets the key used to store the deployment name in the <see cref="Attributes"/> dictionary.
    /// </summary>
    internal static string DeploymentNameKey => "DeploymentName";

    /// <summary>
    /// Model Id or Deployment Name
    /// </summary>
    internal string DeploymentOrModelName { get; set; } = string.Empty;

    /// <summary>
    /// Azure OpenAI Client
    /// </summary>
    internal AzureOpenAIClient Client { get; }

    /// <summary>
    /// Azure OpenAI API endpoint.
    /// </summary>
    internal Uri? Endpoint { get; set; } = null;

    /// <summary>
    /// Logger instance
    /// </summary>
    internal ILogger Logger { get; set; }

    /// <summary>
    /// Storage for AI service attributes.
    /// </summary>
    internal Dictionary<string, object?> Attributes { get; } = [];

    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string deploymentName,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        Verify.NotNullOrWhiteSpace(apiKey);

        var options = GetAzureOpenAIClientOptions(httpClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.DeploymentOrModelName = deploymentName;
        this.Endpoint = new Uri(endpoint);
        this.Client = new AzureOpenAIClient(this.Endpoint, apiKey, options);

        this.AddAttribute(DeploymentNameKey, deploymentName);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");

        var options = GetAzureOpenAIClientOptions(httpClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.DeploymentOrModelName = deploymentName;
        this.Endpoint = new Uri(endpoint);
        this.Client = new AzureOpenAIClient(this.Endpoint, credential, options);

        this.AddAttribute(DeploymentNameKey, deploymentName);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ClientCore"/> class..
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="AzureOpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal ClientCore(
        string deploymentName,
        AzureOpenAIClient openAIClient,
        ILogger? logger = null)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNull(openAIClient);

        this.Logger = logger ?? NullLogger.Instance;
        this.DeploymentOrModelName = deploymentName;
        this.Client = openAIClient;

        this.AddAttribute(DeploymentNameKey, deploymentName);
    }

    /// <summary>Gets options to use for an OpenAIClient</summary>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>An instance of <see cref="OpenAIClientOptions"/>.</returns>
    internal static AzureOpenAIClientOptions GetAzureOpenAIClientOptions(HttpClient? httpClient)
    {
        AzureOpenAIClientOptions options = new()
        {
            ApplicationId = HttpHeaderConstant.Values.UserAgent,
        };

        options.AddPolicy(CreateRequestHeaderPolicy(HttpHeaderConstant.Names.SemanticKernelVersion, HttpHeaderConstant.Values.GetAssemblyVersion(typeof(ClientCore))), PipelinePosition.PerCall);

        if (httpClient is not null)
        {
            options.Transport = new HttpClientPipelineTransport(httpClient);
            options.RetryPolicy = new ClientRetryPolicy(maxRetries: 0); // Disable Azure SDK retry policy if and only if a custom HttpClient is provided.
            options.NetworkTimeout = Timeout.InfiniteTimeSpan; // Disable Azure SDK default timeout
        }

        return options;
    }

    internal void AddAttribute(string key, string? value)
    {
        if (!string.IsNullOrEmpty(value))
        {
            this.Attributes.Add(key, value);
        }
    }

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

    private static T RunRequest<T>(Func<T> request)
    {
        try
        {
            return request.Invoke();
        }
        catch (ClientResultException e)
        {
            throw e.ToHttpOperationException();
        }
    }

    private static GenericActionPipelinePolicy CreateRequestHeaderPolicy(string headerName, string headerValue)
    {
        return new GenericActionPipelinePolicy((message) =>
        {
            if (message?.Request?.Headers?.TryGetValue(headerName, out string? _) == false)
            {
                message.Request.Headers.Set(headerName, headerValue);
            }
        });
    }
}
