// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines an attribute to mark a property on a record class as the key under which the record is stored in a vector store.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordKeyAttribute : Attribute
{
    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// </remarks>
    public string? StoragePropertyName { get; init; }
}
