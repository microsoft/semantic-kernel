// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Attribute to mark a property on a record class as the vector.
/// </summary>
[Experimental("SKEXP0001")]
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorStoreRecordVectorAttribute : Attribute
{
    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// E.g. the property name might be "MyProperty" but the storage name might be "my_property".
    /// </summary>
    public string? StoragePropertyName { get; set; }
}
