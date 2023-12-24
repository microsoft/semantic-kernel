// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Runtime.CompilerServices;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Core implementation for Azure OpenAI clients, providing common functionality and properties.
/// </summary>
internal sealed class AzureOpenAIClientCore : ClientCore
{
    /// <summary>
    /// Gets the key used to store the deployment name in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string DeploymentNameKey => "DeploymentName";

    /// <summary>
    /// OpenAI / Azure OpenAI Client
    /// </summary>
    internal override OpenAIClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIClientCore"/> class using API Key authentication.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureOpenAIClientCore(
        string deploymentName,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");
        Verify.NotNullOrWhiteSpace(apiKey);

        var options = GetOpenAIClientOptions(httpClient);

        this.DeploymentOrModelName = deploymentName;
        this.Client = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(apiKey), options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIClientCore"/> class supporting AAD authentication.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureOpenAIClientCore(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure OpenAI endpoint must start with 'https://'");

        var options = GetOpenAIClientOptions(httpClient);

        this.DeploymentOrModelName = deploymentName;
        this.Client = new OpenAIClient(new Uri(endpoint), credential, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIClientCore"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureOpenAIClientCore(
        string deploymentName,
        OpenAIClient openAIClient,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNull(openAIClient);

        this.DeploymentOrModelName = deploymentName;
        this.Client = openAIClient;

        this.AddAttribute(DeploymentNameKey, deploymentName);
    }

    /// <summary>
    /// Logs Azure OpenAI action details.
    /// </summary>
    /// <param name="callerMemberName">Caller member name. Populated automatically by runtime.</param>
    internal void LogActionDetails([CallerMemberName] string? callerMemberName = default)
    {
        if (this.Logger.IsEnabled(LogLevel.Information))
        {
            this.Logger.LogInformation("Action: {Action}. Azure OpenAI Deployment Name: {DeploymentName}.", callerMemberName, this.DeploymentOrModelName);
        }
    }
}
