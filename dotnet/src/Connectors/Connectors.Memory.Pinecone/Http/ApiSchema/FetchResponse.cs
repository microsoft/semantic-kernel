// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable CA1812 // remove class never instantiated (used by System.Text.Json)

/// <summary>
/// FetchResponse
/// See https://docs.pinecone.io/reference/fetch
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class FetchResponse
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FetchResponse" /> class.
    /// </summary>
    /// <param name="vectors">vectors.</param>
    /// <param name="nameSpace">An index namespace name.</param>
    [JsonConstructor]
    public FetchResponse(Dictionary<string, PineconeDocument> vectors, string nameSpace = "")
    {
        this.Vectors = vectors;
        this.Namespace = nameSpace;
    }

    /// <summary>
    /// Gets or Sets Vectors
    /// </summary>
    [JsonPropertyName("vectors")]
    public Dictionary<string, PineconeDocument> Vectors { get; set; }

    public IEnumerable<PineconeDocument> WithoutEmbeddings()
    {
        return this.Vectors.Values.Select(v => PineconeDocument.Create(v.Id).WithMetadata(v.Metadata));
    }

    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Namespace { get; set; }
}
