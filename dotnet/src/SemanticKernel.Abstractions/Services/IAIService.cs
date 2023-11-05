// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents an empty interface for AI services.
/// </summary>
[SuppressMessage("Design", "CA1040:Avoid empty interfaces")]
public interface IAIService
{
    /// <summary>
    /// Model identifier.
    /// This identifies the AI model these settings are configured for e.g., gpt-4, gpt-3.5-turbo
    /// </summary>
    string? ModelId { get; }

    /// <summary>
    /// Gets the AI service metadata.
    /// </summary>
    IReadOnlyDictionary<string, string> Metadata { get; }
}
