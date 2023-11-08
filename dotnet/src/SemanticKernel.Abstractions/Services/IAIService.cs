// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents an empty interface for AI services.
/// </summary>
public interface IAIService
{
    /// <summary>
    /// Gets the AI service attributes.
    /// </summary>
    T? GetAttributes<T>() where T : AIServiceAttributes;
}
