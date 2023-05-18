// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Service configuration.
/// </summary>
public interface IServiceConfig
{
    /// <summary>
    /// An identifier used to map semantic functions to AI connectors,
    /// decoupling prompts configurations from the actual model and AI provider used.
    /// </summary>
    public string ServiceId { get; }
}
