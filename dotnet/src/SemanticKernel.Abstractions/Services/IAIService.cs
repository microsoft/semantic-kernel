// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents an empty interface for AI services.
/// </summary>
public interface IAIService
{
    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    string? ModelId { get; }

    /// <summary>
    /// Gets the AI service attributes.
    /// </summary>
    IReadOnlyDictionary<string, object> Attributes { get; }
}
