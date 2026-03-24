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
public abstract class PropertyModel(string modelName, Type type) : IPropertyModel
{
    private string? _storageName;
    private Func<object, object?>? _getter;
    private Action<object, object?>? _setter;

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
    /// Gets or sets a dictionary of provider-specific annotations for this property.
    /// </summary>
    /// <remarks>
    /// This allows setting database-specific configuration options that aren't universal across all vector stores.
    /// </remarks>
    public Dictionary<string, object?>? ProviderAnnotations { get; set; }

    IReadOnlyDictionary<string, object?>? IPropertyModel.ProviderAnnotations => this.ProviderAnnotations;

    /// <summary>
    /// Gets whether the property type is nullable. For value types, this is <see langword="true"/> when the type is
    /// <see cref="Nullable{T}"/>. For reference types on .NET 6+, this uses NRT annotations via
    /// <c>NullabilityInfoContext</c> when a <see cref="PropertyInfo"/> is available
    /// (i.e., POCO mapping); otherwise, reference types are assumed nullable.
    /// </summary>
    public bool IsNullable
    {
        get
        {
            // Value types: nullable only if Nullable<T>
            if (this.Type.IsValueType)
            {
                return Nullable.GetUnderlyingType(this.Type) is not null;
            }

            // Reference types: check NRT annotation via NullabilityInfoContext when available
#if NET
            if (this.PropertyInfo is { } propertyInfo)
            {
                var nullabilityInfo = new NullabilityInfoContext().Create(propertyInfo);
                return nullabilityInfo.ReadState != NullabilityState.NotNull;
            }
#endif

            // Dynamic mapping or old framework: assume nullable for reference types
            return true;
        }
    }

    /// <summary>
    /// Configures the property accessors using a CLR <see cref="System.Reflection.PropertyInfo"/> for POCO mapping.
    /// </summary>
    // TODO: Implement compiled delegates for better performance, #11122
    // TODO: Implement source-generated accessors for NativeAOT, #10256
    internal void ConfigurePocoAccessors(PropertyInfo propertyInfo)
    {
        this.PropertyInfo = propertyInfo;
        this._getter = propertyInfo.GetValue;
        this._setter = (record, value) =>
        {
            // If the value is null, no need to set the property (it's the CLR default)
            if (value is not null)
            {
                propertyInfo.SetValue(record, value);
            }
        };
    }

    /// <summary>
    /// Configures the property accessors for dynamic mapping using <see cref="Dictionary{TKey, TValue}"/>.
    /// </summary>
    internal void ConfigureDynamicAccessors()
    {
        var modelName = this.ModelName;
        var propertyType = this.Type;

        this._getter = record =>
        {
            var dictionary = (Dictionary<string, object?>)record;
            var value = dictionary.TryGetValue(modelName, out var tempValue) ? tempValue : null;

            if (value is not null && value.GetType() != (Nullable.GetUnderlyingType(propertyType) ?? propertyType))
            {
                throw new InvalidCastException($"Property '{modelName}' has a value of type '{value.GetType().Name}', but its configured type is '{propertyType.Name}'.");
            }

            return value;
        };

        this._setter = (record, value) => ((Dictionary<string, object?>)record)[modelName] = value;
    }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>, returning the value as an <see cref="object"/>.
    /// </summary>
    public object? GetValueAsObject(object record)
    {
        Debug.Assert(this._getter is not null, "Property accessors have not been configured.");
        return this._getter!(record);
    }

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>, accepting the value to write as an <see cref="object"/>.
    /// </summary>
    public void SetValueAsObject(object record, object? value)
    {
        Debug.Assert(this._setter is not null, "Property accessors have not been configured.");
        this._setter!(record, value);
    }

    /// <summary>
    /// Reads the property from the given <paramref name="record"/>.
    /// </summary>
    // TODO: actually implement the generic accessors to avoid boxing, and make use of them in connectors
    public T GetValue<T>(object record)
        => (T)(object)this.GetValueAsObject(record)!;

    /// <summary>
    /// Writes the property from the given <paramref name="record"/>.
    /// </summary>
    // TODO: actually implement the generic accessors to avoid boxing, and make use of them in connectors
    public void SetValue<T>(object record, T value)
        => this.SetValueAsObject(record, value);
}
