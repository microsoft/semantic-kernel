// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Model;

/// <summary>
/// Vector sparse data. Represented as a list of indices and a list of corresponded values, which must be the same length.
/// </summary>
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
    [JsonConverter(typeof(ReadOnlyMemoryConverter))]
    public ReadOnlyMemory<float> Values { get; set; }

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
