// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable CA1812 // remove class never instantiated (used by System.Text.Json)

/// <summary>
/// QueryResponse
/// See https://docs.pinecone.io/reference/query
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class QueryResponse
{
    /// <summary>
    /// Initializes a new instance of the <see cref="QueryResponse" /> class.
    /// </summary>
    /// <param name="matches">matches.</param>
    /// <param name="nameSpace">An index namespace name.</param>
    public QueryResponse(List<PineconeDocument> matches, string? nameSpace = default)
    {
        this.Matches = matches;
        this.Namespace = nameSpace;
    }

    /// <summary>
    /// Gets or Sets Matches
    /// </summary>
    [JsonPropertyName("matches")]
    public List<PineconeDocument> Matches { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    /// <value>An index namespace name</value>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }
}
