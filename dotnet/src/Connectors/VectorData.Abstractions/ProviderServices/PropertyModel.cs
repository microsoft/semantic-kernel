// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public abstract class PropertyModel(string modelName, Type type)
{
    private string? _storageName;

    /// <summary>
    /// Gets or sets the model name of the property. If the property corresponds to a .NET property, this name is the name of that property.
    /// </summary>
    public string ModelName { get; set; } = modelName;

    /// <summary>
    /// Gets or sets the storage name of the property. This is the name to which the property is mapped in the vector store.
    /// </summary>
    public string StorageName
    {
        get => this._storageName ?? this.ModelName;
        set => this._storageName = value;
    }

    // See comment in VectorStoreJsonModelBuilder
    // TODO: Spend more time thinking about this, there may be a less hacky way to handle it.

    /// <summary>
    /// Gets or sets the temporary storage name for the property, for use during the serialization process by certain connectors.
    /// </summary>
    [Experimental("MEVD9001")]
    public string? TemporaryStorageName { get; set; }

    /// <summary>
    /// Gets or sets the CLR type of the property.
    /// </summary>
    public Type Type { get; set; } = type;

    /// <summary>
    /// Gets or sets the reflection <see cref="PropertyInfo"/> for the .NET property.
    /// </summary>
    /// <value>
    /// The reflection <see cref="PropertyInfo"/> for the .NET property.
    /// <see langword="null"/> when using dynamic mapping.
    /// </value>
    public PropertyInfo? PropertyInfo { get; set; }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>, returning the value as an <see cref="object"/>.
    /// </summary>
    public virtual object? GetValueAsObject(object record)
    {
        if (this.PropertyInfo is null)
        {
            if (record is Dictionary<string, object?> dictionary)
            {
                var value = dictionary.TryGetValue(this.ModelName, out var tempValue)
                    ? tempValue
                    : null;

                if (value is not null && value.GetType() != (Nullable.GetUnderlyingType(this.Type) ?? this.Type))
                {
                    throw new InvalidCastException($"Property '{this.ModelName}' has a value of type '{value.GetType().Name}', but its configured type is '{this.Type.Name}'.");
                }

                return value;
            }

            throw new UnreachableException("Non-dynamic mapping but PropertyInfo is null.");
        }

        // We have a CLR property (non-dynamic POCO mapping)

        // TODO: Implement compiled delegates for better performance, #11122
        // TODO: Implement source-generated accessors for NativeAOT, #10256

        return this.PropertyInfo.GetValue(record);
    }

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>, accepting the value to write as an <see cref="object"/>.
    /// </summary>s
    public virtual void SetValueAsObject(object record, object? value)
    {
        if (this.PropertyInfo is null)
        {
            if (record.GetType() == typeof(Dictionary<string, object?>))
            {
                var dictionary = (Dictionary<string, object?>)record;
                dictionary[this.ModelName] = value;
                return;
            }

            throw new UnreachableException("Non-dynamic mapping but ClrProperty is null.");
        }

        // We have a CLR property (non-dynamic POCO mapping)

        // TODO: Implement compiled delegates for better performance, #11122
        // TODO: Implement source-generated accessors for NativeAOT, #10256

        // If the value is null, no need to set the property (it's the CLR default)
        if (value is not null)
        {
            this.PropertyInfo.SetValue(record, value);
        }
    }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>.
    /// </summary>
    // TODO: actually implement the generic accessors to avoid boxing, and make use of them in connectors
    public virtual T GetValue<T>(object record)
        => (T)(object)this.GetValueAsObject(record)!;

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>.
    /// </summary>s
    // TODO: actually implement the generic accessors to avoid boxing, and make use of them in connectors
    public virtual void SetValue<T>(object record, T value)
    {
        this.SetValueAsObject(record, value);
    }
}
