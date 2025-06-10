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
    /// <param name="name">The name of the property on the data model. If the record is mapped to a .NET type, this corresponds to the .NET property name on that type.</param>
    /// <param name="type">The type of the property.</param>
    private protected VectorStoreProperty(string name, Type? type)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Value cannot be null or whitespace.", nameof(name));
        }

        this.Name = name;
        this.Type = type;
    }

    private protected VectorStoreProperty(VectorStoreProperty source)
    {
        this.Name = source.Name;
        this.StorageName = source.StorageName;
        this.Type = source.Type;
    }

    /// <summary>
    /// Gets or sets the name of the property on the data model.
    /// </summary>
    public string Name { get; set; }

    /// <summary>
    /// Gets or sets an optional name to use for the property in storage, if different from the property name.
    /// </summary>
    /// <remarks>
    /// For example, the property name might be "MyProperty" and the storage name might be "my_property".
    /// This property is only respected by implementations that don't support a well-known
    /// serialization mechanism like JSON, in which case the attributes used by that serialization system will
    /// be used.
    /// </remarks>
    public string? StorageName { get; set; }

    /// <summary>
    /// Gets or sets the type of the property.
    /// </summary>
    public Type? Type { get; set; }
}
