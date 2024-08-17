// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A description of a key property for storage in a memory store.
/// </summary>
[Experimental("SKEXP0001")]
public sealed class MemoryRecordKeyProperty : MemoryRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryRecordKeyProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    public MemoryRecordKeyProperty(string propertyName)
        : base(propertyName)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryRecordKeyProperty"/> class by cloning the given source.
    /// </summary>
    /// <param name="source">The source to clone</param>
    public MemoryRecordKeyProperty(MemoryRecordKeyProperty source)
        : base(source.PropertyName)
    {
    }
}
