// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable CA1812 // remove class never instantiated (used by System.Text.Json)

/// <summary>
/// UpsertResponse
/// See https://docs.pinecone.io/reference/upsert
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
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
