// Copyright (c) Microsoft. All rights reserved.

namespace OpenAIRealtime;

/// <summary>
/// Configuration for Azure OpenAI service.
/// </summary>
public class AzureOpenAIOptions
{
    public const string SectionName = "AzureOpenAI";

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
    public string ApiKey { get; set; }

    public bool IsValid =>
        !string.IsNullOrWhiteSpace(this.DeploymentName) &&
        !string.IsNullOrWhiteSpace(this.Endpoint) &&
        !string.IsNullOrWhiteSpace(this.ApiKey);
}
