// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// A description of a property for storage in a memory store.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class MemoryRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="MemoryRecordProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    private protected MemoryRecordProperty(string propertyName)
    {
        this.PropertyName = propertyName;
    }

    /// <summary>
    /// Gets or sets the name of the property.
    /// </summary>
    public string PropertyName { get; set; }
}
