// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines an attribute to mark a property on a record class as 'data'.
/// </summary>
/// <remarks>
/// Marking a property as 'data' means that the property is not a key and not a vector. But optionally,
/// this property can have an associated vector field containing an embedding for this data.
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordDataAttribute : Attribute
{
    /// <summary>
    /// Gets or sets a value indicating whether this data property is filterable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    [Obsolete("This property is now obsolete and will have no affect if used. Please use IsIndexed instead", error: true)]
    public bool IsFilterable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is full text searchable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    [Obsolete("This property is now obsolete and will have no affect if used. Please use IsFullTextIndexed instead", error: true)]
    public bool IsFullTextSearchable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsIndexed { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is indexed for full-text search.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFullTextIndexed { get; init; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// </remarks>
    public string? StoragePropertyName { get; init; }
}
