// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Defines a base property class for properties on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here will influence how the property is treated by the vector store.
/// </remarks>
[Experimental("SKEXP0001")]
public abstract class VectorStoreRecordProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreRecordProperty"/> class.
    /// </summary>
    /// <param name="dataModelPropertyName">The name of the property on the data model.</param>
    /// <param name="propertyType">The type of the property.</param>
    private protected VectorStoreRecordProperty(string dataModelPropertyName, Type propertyType)
    {
        Verify.NotNullOrWhiteSpace(dataModelPropertyName);
        Verify.NotNull(propertyType);

        this.DataModelPropertyName = dataModelPropertyName;
        this.PropertyType = propertyType;
    }

    private protected VectorStoreRecordProperty(VectorStoreRecordProperty source)
    {
        this.DataModelPropertyName = source.DataModelPropertyName;
        this.StoragePropertyName = source.StoragePropertyName;
        this.PropertyType = source.PropertyType;
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

    /// <summary>
    /// Gets or sets the type of the property.
    /// </summary>
    public Type PropertyType { get; private set; }
}
