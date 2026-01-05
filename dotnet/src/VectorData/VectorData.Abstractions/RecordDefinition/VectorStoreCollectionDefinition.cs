// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
#if !UNITY
#endif

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Describes the properties of a record in a vector store collection.
/// </summary>
/// <remarks>
/// Each property contains additional information about how the property will be treated by the vector store.
/// </remarks>
public sealed class VectorStoreCollectionDefinition
{
    private IList<VectorStoreProperty>? _properties;

    /// <summary>
    /// Gets or sets the list of properties that are stored in the record.
    /// </summary>
    [AllowNull]
    public IList<VectorStoreProperty> Properties
    {
        get => this._properties ??= [];
        set => this._properties = value;
    }

    /// <summary>
    /// Gets or sets the default embedding generator for vector properties in this collection.
    /// </summary>
#if !UNITY
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }
#else
    public object? EmbeddingGenerator { get; set; }
#endif
}
