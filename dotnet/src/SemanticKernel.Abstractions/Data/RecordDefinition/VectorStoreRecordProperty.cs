// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// A description of a property on a record for storage in a vector store.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordProperty"/> class.
    /// </summary>
    /// <param name="propertyName">The name of the property.</param>
    private protected VectorStoreRecordProperty(string propertyName)
    {
        this.PropertyName = propertyName;
    }

    /// <summary>
    /// Gets or sets the name of the property.
    /// </summary>
    public string PropertyName { get; set; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// E.g. the property name might be "MyProperty" but the storage name might be "my_property".
    /// </summary>
    public string? StoragePropertyName { get; set; }
}
