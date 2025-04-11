// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// UpsertRequest
/// See https://docs.pinecone.io/reference/upsert
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class UpsertRequest
{
    /// <summary>
    /// The vectors to upsert
    /// </summary>
    [JsonPropertyName("vectors")]
    public List<PineconeDocument> Vectors { get; set; }

    /// <summary>
    /// An index namespace name
    /// </summary>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

    public static UpsertRequest UpsertVectors(IEnumerable<PineconeDocument> vectorRecords)
    {
        UpsertRequest request = new();

        request.Vectors.AddRange(vectorRecords);

        return request;
    }

    public UpsertRequest ToNamespace(string? indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage request = HttpRequest.CreatePostRequest("/vectors/upsert", this);

        request.Headers.Add("accept", "application/json");

        return request;
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private UpsertRequest()
    {
        this.Vectors = [];
    }

    #endregion
}
