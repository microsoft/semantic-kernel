// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Index namespace parameters.
/// </summary>
public class IndexNamespaceStats
{
    /// <summary>
    /// Initializes a new instance of the <see cref="IndexNamespaceStats" /> class.
    /// </summary>
    /// <param name="vectorCount">vectorCount.</param>
    public IndexNamespaceStats(long vectorCount = default)
    {
        this.VectorCount = vectorCount;
    }

    /// <summary>
    /// The number of vectors in the namespace
    /// </summary>
    [JsonPropertyName("vectorCount")]
    public long VectorCount { get; }
}
