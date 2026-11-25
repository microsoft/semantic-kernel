// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Google;

#pragma warning disable CA1707 // Identifiers should not contain underscores

/// <summary>
/// Represents the version of the Vertex AI API.
/// </summary>
[Obsolete("The Microsoft.SemanticKernel.Connectors.Google package is obsolete. Use the Google.GenAI SDK directly with Microsoft.Extensions.AI (IChatClient and IEmbeddingGenerator) instead.")]
public enum VertexAIVersion
{
    /// <summary>
    /// Represents the V1 version of the Vertex AI API.
    /// </summary>
    V1,

    /// <summary>
    /// Represents the V1-beta version of the Vertex AI API.
    /// </summary>
    V1_Beta
}
