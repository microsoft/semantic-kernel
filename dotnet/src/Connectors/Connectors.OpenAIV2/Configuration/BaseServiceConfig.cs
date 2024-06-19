// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Base service options definition.
/// </summary>
public abstract class BaseServiceConfig
{
    /// <summary>
    /// Model name.
    /// </summary>
    public string? ModelId { get; init; }

    /// <summary>
    /// Service Id.
    /// </summary>
    public string? ServiceId { get; init; }
}
