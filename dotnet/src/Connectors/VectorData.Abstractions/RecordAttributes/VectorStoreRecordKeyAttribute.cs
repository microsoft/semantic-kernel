// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Attribute to mark a property on a record class as the key under which the record is stored in a vector store.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordKeyAttribute : Attribute
{
    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// E.g. the property name might be "MyProperty" but the storage name might be "my_property".
    /// </summary>
    public string? StoragePropertyName { get; set; }
}
