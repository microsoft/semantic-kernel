// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using System.Runtime.CompilerServices;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Base class for OpenAI clients, providing common functionality and properties.
/// </summary>
/// <example>
/// <code>
/// var openAIClient = new CustomOpenAIClient("modelId", "apiKey", "organization");
/// </code>
/// </example>
public abstract class OpenAIClientBase : ClientBase
{
    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    private protected override OpenAIClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientBase"/> class.
    /// </summary>
    /// <param name="modelId">Model name.</param>
    /// <param name="apiKey">OpenAI API Key.</param>
    /// <param name="organization">OpenAI Organization Id (usually optional).</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    private protected OpenAIClientBase(
        string modelId,
        string apiKey,
        string? organization = null,
        HttpClient? httpClient = null,
        ILoggerFactory? loggerFactory = null) : base(loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        this.ModelId = modelId;

        var options = GetClientOptions();
        if (httpClient != null)
        {
            options.Transport = new HttpClientTransport(httpClient);
        }

        if (!string.IsNullOrWhiteSpace(organization))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", organization!), HttpPipelinePosition.PerCall);
        }

        this.Client = new OpenAIClient(apiKey, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientBase"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="modelId">Azure OpenAI model ID or deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    private protected OpenAIClientBase(
        string modelId,
        OpenAIClient openAIClient,
        ILoggerFactory? loggerFactory = null) : base(loggerFactory)
    {
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNull(openAIClient);

        this.ModelId = modelId;
        this.Client = openAIClient;
    }

    /// <summary>
    /// Logs OpenAI action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    private protected void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        this.Logger.LogInformation("Action: {Action}. OpenAI Model ID: {ModelId}.", callerMemberName, this.ModelId);
    }

    /// <summary>
    /// Options used by the OpenAI client, e.g. User Agent.
    /// </summary>
    /// <returns>An instance of <see cref="OpenAIClientOptions"/> with the configured options.</returns>
    private static OpenAIClientOptions GetClientOptions()
    {
        return new OpenAIClientOptions
        {
            Diagnostics =
            {
                IsTelemetryEnabled = Telemetry.IsTelemetryEnabled,
                ApplicationId = Telemetry.HttpUserAgent,
            }
        };
    }
}
