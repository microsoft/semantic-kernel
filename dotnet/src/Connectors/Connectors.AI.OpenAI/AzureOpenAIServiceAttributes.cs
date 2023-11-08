// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Azure OpenAI AI service attributes.
/// </summary>
public class AzureOpenAIServiceAttributes : AIServiceAttributes
{
    /// <summary>
    /// Deployment Name.
    /// </summary>
    public string? DeploymentName { get; init; }

    /// <summary>
    /// Endpoint.
    /// </summary>
    public string? Endpoint { get; init; }

    /// <summary>
    /// API Version.
    /// </summary>
    public string? ApiVersion { get; init; }
}
