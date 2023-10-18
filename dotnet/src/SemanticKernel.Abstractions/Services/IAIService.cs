// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents an empty interface for AI services.
/// </summary>
[SuppressMessage("Design", "CA1040:Avoid empty interfaces")]
public interface IAIService
{
    /// <summary>
    /// Service identifier.
    /// This identifies a service and is set when the AI service is registered.
    /// </summary>
    string? ServiceId { get; }
}
