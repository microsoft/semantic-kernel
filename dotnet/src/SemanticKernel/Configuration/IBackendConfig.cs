// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Configuration;

/// <summary>
/// Backend configuration.
/// </summary>
public interface IBackendConfig
{
    /// An identifier used to map semantic functions to backend,
    /// decoupling prompts configurations from the actual model used.
    public string Label { get; }
}
