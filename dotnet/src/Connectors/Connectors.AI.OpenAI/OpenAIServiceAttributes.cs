// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// OpenAI AI service attributes.
/// </summary>
public class OpenAIServiceAttributes : AIServiceAttributes
{
    /// <summary>
    /// Organization key.
    /// </summary>
    public const string OrganizationKey = "Organization";

    /// <summary>
    /// Organization.
    /// </summary>
    public string? Organization
    {
        get => this.InternalAttributes.TryGetValue(OrganizationKey, out var value) ? value as string : null;
        init => this.InternalAttributes[OrganizationKey] = value ?? string.Empty;
    }
}
