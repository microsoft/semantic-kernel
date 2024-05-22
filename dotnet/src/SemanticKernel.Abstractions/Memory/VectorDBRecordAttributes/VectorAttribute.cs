// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Attribute to mark a property on a vector model class as the vector.
/// </summary>
[Experimental("SKEXP0001")]
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class VectorAttribute : Attribute
{
    /// <summary>
    /// Gets or sets the name of a related property in the data model that is storing the data that this vector is indexing.
    /// </summary>
    public string? DataPropertyName { get; set; }
}
