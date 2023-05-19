// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone.Http.ApiSchema;

#pragma warning disable CA1812 // remove class never instantiated (used by System.Text.Json)

/// <summary>
/// UpsertResponse
/// See https://docs.pinecone.io/reference/upsert
/// </summary>
internal sealed class UpsertResponse
{
    /// <summary>
    /// Initializes a new instance of the <see cref="UpsertResponse" /> class.
    /// </summary>
    /// <param name="upsertedCount">upsertedCount.</param>
    public UpsertResponse(int upsertedCount = default)
    {
        this.UpsertedCount = upsertedCount;
    }

    /// <summary>
    /// Gets or Sets UpsertedCount
    /// </summary>
    [JsonPropertyName("upsertedCount")]
    public int UpsertedCount { get; set; }
}
