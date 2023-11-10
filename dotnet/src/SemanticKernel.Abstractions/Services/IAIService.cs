// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents an empty interface for AI services.
/// </summary>
public interface IAIService
{
    /// <summary>
    /// Gets the AI service attributes.
    /// </summary>
    IReadOnlyDictionary<string, string> Attributes { get; }
}
