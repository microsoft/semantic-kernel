// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a base property class for properties on a vector store record.
/// </summary>
/// <remarks>
/// The characteristics defined here influence how the property is treated by the vector store.
/// </remarks>
public abstract class VectorStoreProperty
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorStoreProperty"/> class.
    /// </summary>
    /// <param name="dataModelPropertyName">The name of the property on the data model.</param>
    /// <param name="propertyType">The type of the property.</param>
    private protected VectorStoreProperty(string dataModelPropertyName, Type propertyType)
    {
        if (string.IsNullOrWhiteSpace(dataModelPropertyName))
        {
            throw new ArgumentException("Value cannot be null or whitespace.", nameof(dataModelPropertyName));
        }

        if (propertyType == null)
        {
            throw new ArgumentNullException(nameof(propertyType));
        }

        this.DataModelPropertyName = dataModelPropertyName;
        this.PropertyType = propertyType;
    }

    private protected VectorStoreProperty(VectorStoreProperty source)
    {
        this.DataModelPropertyName = source.DataModelPropertyName;
        this.StoragePropertyName = source.StoragePropertyName;
        this.PropertyType = source.PropertyType;
    }

    /// <summary>
    /// Gets the name of the property on the data model.
    /// </summary>
    public string DataModelPropertyName { get; private set; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// This property is only respected by implementations that do not support a well-known
    /// serialization mechanism like JSON, in which case the attributes used by that serialization system will
    /// be used.
    /// </remarks>
    public string? StoragePropertyName { get; init; }

    /// <summary>
    /// Gets the type of the property.
    /// </summary>
    public Type PropertyType { get; private set; }
}
