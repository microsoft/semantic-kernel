// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// AI model request settings.
/// </summary>
public interface IAIRequestSettings
{
    /// <summary>
    /// An identifier used to map semantic functions to AI connectors,
    /// decoupling prompts configurations from the actual model and AI provider used.
    /// </summary>
    public string ServiceId { get; }
}
