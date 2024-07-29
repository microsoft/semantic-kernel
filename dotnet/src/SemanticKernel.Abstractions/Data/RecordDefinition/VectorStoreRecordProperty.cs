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
    /// <param name="dataModelPropertyName">The name of the property on the data model.</param>
    private protected VectorStoreRecordProperty(string dataModelPropertyName)
    {
        this.DataModelPropertyName = dataModelPropertyName;
    }

    private protected VectorStoreRecordProperty(VectorStoreRecordProperty source)
    {
        this.DataModelPropertyName = source.DataModelPropertyName;
        this.StoragePropertyName = source.StoragePropertyName;
    }

    /// <summary>
    /// Gets or sets the name of the property on the data model.
    /// </summary>
    public string DataModelPropertyName { get; private set; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// E.g. the property name might be "MyProperty" but the storage name might be "my_property".
    /// This property will only be respected by implementations that do not support a well known
    /// serialization mechanism like JSON, in which case the attributes used by that seriallization system will
    /// be used.
    /// </summary>
    public string? StoragePropertyName { get; init; }
}
