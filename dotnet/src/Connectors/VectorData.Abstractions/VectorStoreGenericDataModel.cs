// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a generic data model that can be used to store and retrieve any data from a vector store.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <param name="key">The key of the record.</param>
public sealed class VectorStoreGenericDataModel<TKey>(TKey key)
{
    /// <summary>
    /// Gets or sets the key of the record.
    /// </summary>
    public TKey Key { get; set; } = key;

    /// <summary>
    /// Gets or sets a dictionary of data items stored in the record.
    /// </summary>
    /// <remarks>
    /// This dictionary contains all fields that aren't vectors.
    /// </remarks>
    public Dictionary<string, object?> Data { get; init; } = new();

    /// <summary>
    /// Gets or sets a dictionary of vectors stored in the record.
    /// </summary>
    public Dictionary<string, object?> Vectors { get; init; } = new();
}
