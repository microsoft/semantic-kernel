// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// The Update operation updates vector in a namespace.
/// If a value is included, it will overwrite the previous value.
/// If a set_metadata is included, the values of the fields specified in it will be added or overwrite the previous value.
/// See https://docs.pinecone.io/reference/update
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
internal sealed class UpdateVectorRequest
{
    /// <summary>
    /// The vectors unique ID
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }

    /// <summary>
    ///  The sparse vector data
    /// </summary>
    [JsonPropertyName("sparseValues")]
    public SparseVectorData? SparseValues { get; set; }

    /// <summary>
    /// The metadata to set
    /// </summary>
    [JsonPropertyName("setMetadata")]
    public Dictionary<string, object>? Metadata { get; set; }

    /// <summary>
    /// The namespace the vector belongs to
    /// </summary>
    [JsonPropertyName("namespace")]
    public string? Namespace { get; set; }

    public static UpdateVectorRequest UpdateVector(string id)
    {
        return new UpdateVectorRequest(id);
    }

    public static UpdateVectorRequest FromPineconeDocument(PineconeDocument document)
    {
        return new UpdateVectorRequest(document.Id, document.Values)
        {
            SparseValues = document.SparseValues,
            Metadata = document.Metadata
        };
    }

    public UpdateVectorRequest InNamespace(string? indexNamespace)
    {
        this.Namespace = indexNamespace;
        return this;
    }

    public UpdateVectorRequest SetMetadata(Dictionary<string, object>? setMetadata)
    {
        this.Metadata = setMetadata;
        return this;
    }

    public UpdateVectorRequest UpdateSparseValues(SparseVectorData? sparseValues)
    {
        this.SparseValues = sparseValues;
        return this;
    }

    public UpdateVectorRequest UpdateValues(ReadOnlyMemory<float> values)
    {
        this.Values = values;
        return this;
    }

    public HttpRequestMessage Build()
    {
        HttpRequestMessage? request = HttpRequest.CreatePostRequest(
            "/vectors/update", this);

        request.Headers.Add("accept", "application/json");

        return request;
    }

    #region private ================================================================================

    /// <summary>
    /// Initializes a new instance of the <see cref="UpdateVectorRequest" /> class.
    /// </summary>
    [JsonConstructor]
    private UpdateVectorRequest(string id, ReadOnlyMemory<float> values = default)
    {
        this.Id = id;
        this.Values = values;
    }

    #endregion
}
