// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Extend this class to define the attributes for your AI service.
/// </summary>
public class AIServiceAttributes
{
    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    public string? ModelId { get; init; }
}
