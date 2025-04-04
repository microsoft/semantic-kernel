// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a data property on a vector store record.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordDataPropertyModel(string modelName, Type type) : VectorStoreRecordPropertyModel(modelName, type)
{
    /// <summary>
    /// Gets or sets a value indicating whether this data property is filterable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFilterable { get; set; }

    /// <summary>
    /// Gets or sets a value indicating whether this data property is full text searchable.
    /// </summary>
    /// <value>
    /// The default is <see langword="false" />.
    /// </value>
    public bool IsFullTextSearchable { get; set; }

    /// <inheritdoc/>
    // TODO: Temporary, remove once we move to Dictionary<string, object?> as the dynamic representation
    public override object? GetValueAsObject(object record)
    {
        if (this.PropertyInfo is null)
        {
            var type = record.GetType();

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
            {
                var dataProperty = type.GetProperty("Data")!;
                var dictionary = (Dictionary<string, object?>)dataProperty.GetValue(record)!;
                return dictionary.TryGetValue(this.ModelName, out var value)
                    ? value
                    : null;
            }
        }

        return base.GetValueAsObject(record);
    }

    /// <inheritdoc/>
    // TODO: Temporary, remove once we move to Dictionary<string, object?> as the dynamic representation
    public override void SetValueAsObject(object record, object? value)
    {
        if (this.PropertyInfo is null)
        {
            var type = record.GetType();

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
            {
                var dataProperty = type.GetProperty("Data")!;
                var dictionary = (Dictionary<string, object?>)dataProperty.GetValue(record)!;
                dictionary[this.ModelName] = value;
                return;
            }
        }

        base.SetValueAsObject(record, value);
    }

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Data, {this.Type.Name})";
}
