// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A generic data model that can be used to store and retrieve any data from a vector store.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
/// <param name="key">The key of the record.</param>
[Experimental("SKEXP0001")]
public sealed class VectorStoreGenericDataModel<TKey>(TKey key)
    where TKey : notnull
{
    /// <summary>
    /// Gets or sets the key of the record.
    /// </summary>
    public TKey Key { get; set; } = key;

    /// <summary>
    /// Gets or sets a dictionary of data items stored in the record.
    /// </summary>
    /// <remarks>
    /// This dictionary contains all fields that are not vectors.
    /// </remarks>
    public Dictionary<string, object?> Data { get; init; } = new();

    /// <summary>
    /// Gets or sets a dictionary of vectors stored in the record.
    /// </summary>
    public Dictionary<string, object?> Vectors { get; init; } = new();
}
