// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a generic data model that can be used to store and retrieve any data from a vector store.
/// </summary>
/// <typeparam name="TKey">The data type of the record key.</typeparam>
[Obsolete($"{nameof(VectorStoreGenericDataModel<TKey>)} has been replaced by Dictionary<string, object?>", error: true)]
public sealed class VectorStoreGenericDataModel<TKey>
{
    /// <summary>
    /// Constructs a new <see cref="VectorStoreGenericDataModel{TKey}"/>.
    /// </summary>
#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    public VectorStoreGenericDataModel()
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
    {
    }

    /// <summary>
    /// Constructs a new <see cref="VectorStoreGenericDataModel{TKey}"/>.
    /// </summary>
    public VectorStoreGenericDataModel(TKey key)
    {
        this.Key = key;
    }

    /// <summary>
    /// Gets or sets the key of the record.
    /// </summary>
    public TKey Key { get; set; }

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
