// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Azure OpenAI AI service attributes.
/// </summary>
public class AzureOpenAIServiceAttributes : AIServiceAttributes
{
    /// <summary>
    /// Deployment Name key.
    /// </summary>
    public const string DeploymentNameKey = "DeploymentName";

    /// <summary>
    /// Deployment Name.
    /// </summary>
    public string? DeploymentName
    {
        get => this.InternalAttributes.ContainsKey(DeploymentNameKey) ? this.InternalAttributes[DeploymentNameKey] as string : null;
        init => this.InternalAttributes[DeploymentNameKey] = value ?? string.Empty;
    }
}
