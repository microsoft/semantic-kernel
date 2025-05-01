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
    [VectorStoreKeyProperty]
    public required Guid Key { get; init; }

    /// <summary>
    /// The text content of the record.
    /// </summary>
    [VectorStoreDataProperty]
    public required string Text { get; init; }

    /// <summary>
    /// The embedding for the record.
    /// </summary>
    [VectorStoreVectorProperty(1536)]
    public required ReadOnlyMemory<float> Embedding { get; init; }
}
