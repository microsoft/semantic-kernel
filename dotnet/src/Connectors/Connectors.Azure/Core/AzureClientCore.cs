// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Azure;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.Azure;

/// <summary>
/// Core implementation for Azure clients, providing common functionality and properties.
/// </summary>
internal sealed class AzureClientCore : ClientCore
{
    /// <summary>
    /// Gets the key used to store the deployment name in the <see cref="IAIService.Attributes"/> dictionary.
    /// </summary>
    public static string DeploymentNameKey => "DeploymentName";

    /// <summary>
    /// OpenAI / Azure Client
    /// </summary>
    internal override OpenAIClient Client { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureClientCore"/> class using API Key authentication.
    /// </summary>
    /// <param name="deploymentName">Azure deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureClientCore(
        string deploymentName,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure endpoint must start with 'https://'");
        Verify.NotNullOrWhiteSpace(apiKey);

        var options = GetOpenAIClientOptions(httpClient);

        this.DeploymentOrModelName = deploymentName;
        this.Client = new OpenAIClient(new Uri(endpoint), new AzureKeyCredential(apiKey), options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureClientCore"/> class supporting AAD authentication.
    /// </summary>
    /// <param name="deploymentName">Azure deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="credential">Token credential, e.g. DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, etc.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureClientCore(
        string deploymentName,
        string endpoint,
        TokenCredential credential,
        HttpClient? httpClient = null,
        ILogger? logger = null) : base(logger)
    {
        Verify.NotNullOrWhiteSpace(deploymentName);
        Verify.NotNullOrWhiteSpace(endpoint);
        Verify.StartsWith(endpoint, "https://", "The Azure endpoint must start with 'https://'");

        var options = GetOpenAIClientOptions(httpClient);

        this.DeploymentOrModelName = deploymentName;
        this.Client = new OpenAIClient(new Uri(endpoint), credential, options);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AzureClientCore"/> class using the specified OpenAIClient.
    /// Note: instances created this way might not have the default diagnostics settings,
    /// it's up to the caller to configure the client.
    /// </summary>
    /// <param name="deploymentName">Azure deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="openAIClient">Custom <see cref="OpenAIClient"/>.</param>
    /// <param name="logger">The <see cref="ILogger"/> to use for logging. If null, no logging will be performed.</param>
    internal AzureClientCore(
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
}
