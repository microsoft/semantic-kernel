// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.AI.OpenAI.Services;

/// <summary>
/// Azure OpenAI configuration.
/// </summary>
public sealed class AzureOpenAIConfig : BackendConfig
{
    /// <summary>
    /// Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
    /// </summary>
    public string DeploymentName { get; set; }

    /// <summary>
    /// Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
    /// </summary>
    public string Endpoint { get; set; }

    /// <summary>
    /// Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
    /// </summary>
    public string APIKey { get; set; }

    /// <summary>
    /// Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference
    /// </summary>
    public string APIVersion { get; set; }

    /// <summary>
    /// Creates a new <see cref="AzureOpenAIConfig" /> with supplied values.
    /// </summary>
    /// <param name="label">An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used</param>
    /// <param name="deploymentName">Azure OpenAI deployment name, see https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource</param>
    /// <param name="endpoint">Azure OpenAI deployment URL, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiKey">Azure OpenAI API key, see https://learn.microsoft.com/azure/cognitive-services/openai/quickstart</param>
    /// <param name="apiVersion">Azure OpenAI API version, see https://learn.microsoft.com/azure/cognitive-services/openai/reference</param>
    public AzureOpenAIConfig(string label, string deploymentName, string endpoint, string apiKey, string apiVersion)
        : base(label)
    {
        Verify.NotEmpty(deploymentName, "The deployment name is empty");
        Verify.NotEmpty(endpoint, "The endpoint is empty");
        Verify.StartsWith(endpoint, "https://", "The endpoint URL must start with https://");
        Verify.NotEmpty(apiKey, "The API key is empty");

        this.DeploymentName = deploymentName;
        this.Endpoint = endpoint;
        this.APIKey = apiKey;
        this.APIVersion = apiVersion;
    }
}
