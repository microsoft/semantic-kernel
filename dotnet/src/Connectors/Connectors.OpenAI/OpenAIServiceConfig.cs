// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Required configuration for Azure OpenAI chat completion with data.
/// More information: <see href="https://learn.microsoft.com/azure/cognitive-services/openai/quickstart"/>
/// </summary>
public sealed class OpenAIServiceConfig
{
    /// <summary>
    /// Azure OpenAI deployment name, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource"/>
    /// </summary>
    public string? DeploymentName { get; set; }

    /// <summary>
    /// OpenAI model name, see <see href="https://platform.openai.com/docs/models"/>
    /// </summary>
    public string? ModelId { get; set; }

    /// <summary>
    /// Azure OpenAI deployment URL, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/quickstart"/>
    /// </summary>
    public string? Endpoint { get; set; }

    /// <summary>
    /// Azure OpenAI API key, see <see href="https://learn.microsoft.com/azure/cognitive-services/openai/quickstart"/> or <see href="https://platform.openai.com/docs/api-reference/authentication"/>
    /// </summary>
    public string? ApiKey { get; set; }

    /// <summary>
    /// OpenAI organization id, see <see href="https://platform.openai.com/docs/api-reference/authentication"/>
    /// </summary>
    public string? Organization { get; set; }
}
