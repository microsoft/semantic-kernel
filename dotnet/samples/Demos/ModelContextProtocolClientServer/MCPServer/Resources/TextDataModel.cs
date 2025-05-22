// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace MCPServer.Resources;

/// <summary>
/// A simple data model for a record in the vector store.
/// </summary>
public class TextDataModel
{
    /// <summary>
    /// Unique identifier for the record.
    /// </summary>
    [VectorStoreKey]
    public required Guid Key { get; init; }

    /// <summary>
    /// The text content of the record.
    /// </summary>
    [VectorStoreData]
    public required string Text { get; init; }

    /// <summary>
    /// The embedding for the record.
    /// </summary>
    [VectorStoreVector(1536)]
    public required ReadOnlyMemory<float> Embedding { get; init; }
}
