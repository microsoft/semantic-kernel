// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace;

/// <summary>
/// HuggingFace AI service attributes.
/// </summary>
public class HuggingFaceServiceAttributes : AIServiceAttributes
{
    /// <summary>
    /// Endpoint.
    /// </summary>
    public string? Endpoint { get; init; }
}
