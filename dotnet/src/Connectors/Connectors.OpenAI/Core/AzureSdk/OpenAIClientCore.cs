// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Reflection;
using System.Runtime.CompilerServices;
using System.Threading;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Core implementation for OpenAI clients, providing common functionality and properties.
/// </summary>
internal sealed class OpenAIClientCore : ClientCore
{
    private const string PublicOpenAIApiVersion = "1";
    private const string PublicOpenAIEndpoint = $"https://api.openai.com/v{PublicOpenAIApiVersion}";

    /// <summary>
    /// Gets the attribute name used to store the organization in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string OrganizationKey => "Organization";

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal override OpenAIClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientCore"/> class.
    /// </summary>
    /// <param name="modelId">Model name.</param>
    /// <param name="apiKey">OpenAI API Key.</param>
    /// <param name="endpoint">OpenAI compatible API endpoint.</param>
    /// <param name="organization">OpenAI Organization Id (usually optional).</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAIClientCore(
        string modelId,
        string? apiKey = null,
        Uri? endpoint = null,
        string? organization = null,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);

        this.DeploymentOrModelName = modelId;

        var options = GetOpenAIClientOptions(httpClient);

        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), HttpPipelinePosition.PerCall);
        }

        // Accepts the endpoint if provided, otherwise uses the default OpenAI endpoint.
        var clientEndpoint = endpoint ?? httpClient?.BaseAddress;

        if (clientEndpoint is null)
        {
            Verify.NotNullOrWhiteSpace(apiKey); // For Public OpenAI Endpoint a key must be provided.
            clientEndpoint = new Uri(PublicOpenAIEndpoint);
        }
        else if (clientEndpoint?.PathAndQuery == "/")
        {
            // Adds missing /v1 if not provided.
            clientEndpoint = new Uri($"{endpoint}v1");
        }

        this.Client = new OpenAIClient(clientEndpoint, CreateDelegatedToken(apiKey ?? string.Empty), options);

        this.UpdateOpenAIClientPrivateFields(endpoint, options, apiKey);
    }

    private void UpdateOpenAIClientPrivateFields(Uri? endpoint, OpenAIClientOptions options, string? apiKey = null)
    {
        var type = typeof(OpenAIClient);
        if (endpoint?.Scheme == "http")
        {
            if (apiKey is not null)
            {
                throw new KernelException("To use an APIKey you must provide a TLS protected (https) endpoint");
            }

            // When using Non-HTTPS APIs (local deployments like LM Studio), authentication is not supported by OpenAIClient Pipeline implementation.
            // The current only way is removing the authentication policy thru reflection, to be able to use SDK Azure Client against custom APIs.
            // Otherwise the error bellow will happen:
            // System.InvalidOperationException : Bearer token authentication is not permitted for non TLS protected (https) endpoints.

            var fieldInfo = type.GetField("_pipeline", BindingFlags.NonPublic | BindingFlags.Instance);

            // Change the value of the private field
            fieldInfo?.SetValue(this.Client, HttpPipelineBuilder.Build(options,
                Array.Empty<HttpPipelinePolicy>(),
                Array.Empty<HttpPipelinePolicy>(),
                new ResponseClassifier())
            );
        }

        // Change the value of the private field so RequestUriBuilder method won't append Azure path and query to the base endpoint Uri.
        // <see href="https://github.com/Azure/azure-sdk-for-net/blob/cc45f7e43aac5737f05d802a1fb2c4fa40bd2098/sdk/openai/Azure.AI.OpenAI/src/Custom/OpenAIClient.cs#L931"/>
        var isConfiguredForAzureFieldInfo = type.GetField("_isConfiguredForAzureOpenAI", BindingFlags.NonPublic | BindingFlags.Instance);
        isConfiguredForAzureFieldInfo?.SetValue(this.Client, false);
    }

    private static TokenCredential CreateDelegatedToken(string token)
    {
        AccessToken accessToken = new(token, DateTimeOffset.Now.AddDays(180.0));
        return DelegatedTokenCredential.Create((TokenRequestContext _, CancellationToken _) => accessToken);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientCore"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAIClientCore(
        string modelId,
        OpenAIClient openAIClient,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        this.DeploymentOrModelName = modelId;
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
            this.Logger.LogInformation("Action: {Action}. OpenAI Model ID: {ModelId}.", callerMemberName, this.DeploymentOrModelName);
        }
    }
}
