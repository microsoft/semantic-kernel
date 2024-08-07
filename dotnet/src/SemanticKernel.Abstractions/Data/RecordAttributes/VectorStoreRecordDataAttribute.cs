// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Attribute to mark a property on a record class as 'data'.
/// </summary>
/// <remarks>
/// Marking a property as 'data' means that the property is not a key, and not a vector, but optionally
/// this property may have an associated vector field containing an embedding for this data.
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordDataAttribute : Attribute
{
    /// <summary>
    /// Gets or sets a value indicating whether this data property is filterable.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="false" />.
    /// </remarks>
    public bool IsFilterable { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is full text searchable.
    /// </summary>
    /// <remarks>
    /// Default is <see langword="false" />.
    /// </remarks>
    public bool IsFullTextSearchable { get; init; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// E.g. the property name might be "MyProperty" but the storage name might be "my_property".
    /// </summary>
    public string? StoragePropertyName { get; set; }
}
