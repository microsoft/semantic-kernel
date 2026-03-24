// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Reflection;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <summary>
/// Represents a read-only view of a property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public interface IPropertyModel
{
    /// <summary>
    /// Gets the model name of the property. If the property corresponds to a .NET property, this name is the name of that property.
    /// </summary>
    string ModelName { get; }

    /// <summary>
    /// Gets the storage name of the property. This is the name to which the property is mapped in the vector store.
    /// </summary>
    string StorageName { get; }

    /// <summary>
    /// Gets the CLR type of the property.
    /// </summary>
    Type Type { get; }

    /// <summary>
    /// Gets the reflection <see cref="PropertyInfo"/> for the .NET property.
    /// </summary>
    /// <value>
    /// The reflection <see cref="PropertyInfo"/> for the .NET property.
    /// <see langword="null"/> when using dynamic mapping.
    /// </value>
    PropertyInfo? PropertyInfo { get; }

    /// <summary>
    /// Gets whether the property type is nullable.
    /// </summary>
    bool IsNullable { get; }

    /// <summary>
    /// Gets a dictionary of provider-specific annotations for this property.
    /// </summary>
    IReadOnlyDictionary<string, object?>? ProviderAnnotations { get; }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>, returning the value as an <see cref="object"/>.
    /// </summary>
    object? GetValueAsObject(object record);

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>, accepting the value to write as an <see cref="object"/>.
    /// </summary>
    void SetValueAsObject(object record, object? value);

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>.
    /// </summary>
    T GetValue<T>(object record);

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>.
    /// </summary>
    void SetValue<T>(object record, T value);
}
