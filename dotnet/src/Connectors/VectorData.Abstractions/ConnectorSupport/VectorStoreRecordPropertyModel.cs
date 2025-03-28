// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a property on a vector store record.
/// </summary>
[Experimental("MEVD9001")]
public abstract class VectorStoreRecordPropertyModel(string modelName, Type clrType)
{
    private string? _storageName;

    /// <summary>
    /// The model name of the property. If the property corresponds to a .NET property, this name is the name of that property.
    /// </summary>
    public string ModelName { get; set; } = modelName;

    /// <summary>
    /// The storage name of the property. This is the name to which the property is mapped in the vector store.
    /// </summary>
    public string StorageName
    {
        get => this._storageName ?? this.ModelName;
        set => this._storageName = value;
    }

    // See comment in VectorStoreJsonModelBuilder
    // TODO: Spend more time thinking about this, there may be a less hacky way to handle it.

    /// <summary>
    /// A temporary storage name for the property, for use during the serialization process by certain connectors.
    /// </summary>
    [Experimental("MEVD9001")]
    public string? TemporaryStorageName { get; set; }

    /// <summary>
    /// The CLR type of the property.
    /// </summary>
    public Type ClrType { get; set; } = clrType;

    /// <summary>
    /// The reflection <see cref="ClrProperty"/> for the CLR property.
    /// <see langword="null"/> when using dynamic mapping.
    /// </summary>
    public PropertyInfo? ClrProperty { get; set; }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>, returning the value as an <see cref="object"/>.
    /// </summary>
    // TODO: Temporary, remove virtual once we move to Dictionary<string, object?> as the dynamic representation
    public virtual object? GetValueAsObject(object record)
    {
        if (this.ClrProperty is not null)
        {
            // We have a CLR property (non-dynamic POCO mapping)

            // TODO: Implement compiled delegates for better performance, #11122
            // TODO: Implement source-generated accessors for NativeAOT, #10256

            return this.ClrProperty.GetValue(record);
        }

        throw new UnreachableException("Must be overridden by derived class (for now).");
    }

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>, accepting the value to write as an <see cref="object"/>.
    /// </summary>s
    public virtual void SetValueAsObject(object record, object? value)
    {
        if (this.ClrProperty is not null)
        {
            // We have a CLR property (non-dynamic POCO mapping)

            // TODO: Implement compiled delegates for better performance, #11122
            // TODO: Implement source-generated accessors for NativeAOT, #10256

            // If the value is null, no need to set the property (it's the CLR default)
            if (value is not null)
            {
                this.ClrProperty.SetValue(record, value);
            }

            return;
        }

        throw new UnreachableException("Must be overridden by derived class (for now).");
    }

    // TODO: implement the generic accessors to avoid boxing, and make use of them in connectors
}
