// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// OpenAI AI service attributes.
/// </summary>
public class OpenAIServiceAttributes : AIServiceAttributes
{
    /// <summary>
    /// Organization.
    /// </summary>
    public string? Organization { get; init; }
}
