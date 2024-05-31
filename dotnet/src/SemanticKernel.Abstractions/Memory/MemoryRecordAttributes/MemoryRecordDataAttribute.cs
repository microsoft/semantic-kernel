// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// Attribute to mark a property on a vector model class as the data that is being indexed.
/// </summary>
[Experimental("SKEXP0001")]
[AttributeUsage(AttributeTargets.Property, AllowMultiple = false)]
public sealed class MemoryRecordDataAttribute : Attribute
{
    /// <summary>
    /// Gets or sets a value indicating whether this data field has an associated embedding field.
    /// </summary>
    /// <remarks>Defaults to <see langword="false" /></remarks>
    public bool HasEmbedding { get; init; }

    /// <summary>
    /// Gets or sets the name of the property that contains the embedding for this data field.
    /// </summary>
    public string? EmbeddingPropertyName { get; init; }
}
