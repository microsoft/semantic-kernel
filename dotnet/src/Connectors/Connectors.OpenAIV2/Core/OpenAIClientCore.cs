// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Net.Http;
using System.Runtime.CompilerServices;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.OpenAI.Core.AzureSdk;
using Microsoft.SemanticKernel.Services;
using OpenAI;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Core implementation for OpenAI clients, providing common functionality and properties.
/// </summary>
internal sealed class OpenAIClientCore : ClientCore
{
    private const string DefaultPublicEndpoint = "https://api.openai.com/v1";

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
    /// <param name="config">Client configuration</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAIClientCore(
        OpenAIClientAudioToTextServiceConfig config,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(config.ModelId);

        this.ModelName = config.ModelId;

        var options = GetOpenAIClientOptions(httpClient);

        if (!string.IsNullOrWhiteSpace(config.OrganizationId))
        {
            options.AddPolicy(new AddHeaderRequestPolicy("OpenAI-Organization", config.OrganizationId!), PipelinePosition.PerCall);
        }

        // Accepts the endpoint if provided, otherwise uses the default OpenAI endpoint.
        var providedEndpoint = config.Endpoint ?? httpClient?.BaseAddress;
        if (providedEndpoint is null)
        {
            Verify.NotNullOrWhiteSpace(config.ApiKey); // For Public OpenAI Endpoint a key must be provided.
            this.Endpoint = new Uri(DefaultPublicEndpoint);
        }
        else
        {
            options.AddPolicy(new CustomHostPipelinePolicy(providedEndpoint), PipelinePosition.PerTry);
            this.Endpoint = providedEndpoint;
        }

        this.Client = new OpenAIClient(config.ApiKey ?? string.Empty, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIClientCore"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="config">Client configuration</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal OpenAIClientCore(
        OpenAIAudioToTextServiceConfig config,
        OpenAIClient openAIClient,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(config.ModelId);
        Verify.NotNull(openAIClient);

        this.ModelName = config.ModelId;
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
            this.Logger.LogInformation("Action: {Action}. OpenAI Model ID: {ModelId}.", callerMemberName, this.ModelName);
        }
    }
}
