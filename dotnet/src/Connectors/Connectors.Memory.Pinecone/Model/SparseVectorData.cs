// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Represents a sparse vector data, which is a list of indices and a list of corresponding values, both of the same length.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public class SparseVectorData
{
    /// <summary>
    /// The indices of the sparse data.
    /// </summary>
    /// <value>The indices of the sparse data.</value>
    [JsonPropertyName("indices")]
    public IEnumerable<long> Indices { get; set; }

    /// <summary>
    /// The corresponding values of the sparse data, which must be the same length as the indices.
    /// </summary>
    /// <value>The corresponding values of the sparse data, which must be the same length as the indices.</value>
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="SparseVectorData"/> class with the specified indices and values.
    /// </summary>
    /// <param name="indices">The indices of the sparse data.</param>
    /// <param name="values">The corresponding values of the sparse data, which must be the same length as the indices.</param>
    /// <returns>A new instance of the <see cref="SparseVectorData"/> class.</returns>
    public static SparseVectorData CreateSparseVectorData(List<long> indices, ReadOnlyMemory<float> values)
    {
        return new SparseVectorData(indices, values);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="SparseVectorData" /> class.
    /// </summary>
    /// <param name="indices">The indices of the sparse data. (required).</param>
    /// <param name="values">The corresponding values of the sparse data, which must be the same length as the indices. (required).</param>
    [JsonConstructor]
    public SparseVectorData(List<long> indices, ReadOnlyMemory<float> values)
    {
        this.Indices = indices;
        this.Values = values;
    }
}
