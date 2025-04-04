// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <summary>
/// Represents a key property on a vector store record.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordKeyPropertyModel(string modelName, Type type) : VectorStoreRecordPropertyModel(modelName, type)
{
    /// <inheritdoc/>
    // TODO: Temporary, remove once we move to Dictionary<string, object?> as the dynamic representation
    public override object? GetValueAsObject(object record)
    {
        if (this.PropertyInfo is null)
        {
            var type = record.GetType();

            if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(VectorStoreGenericDataModel<>))
            {
                var keyProperty = type.GetProperty("Key")!;
                return keyProperty.GetValue(record);
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
                var keyProperty = type.GetProperty("Key")!;
                keyProperty.SetValue(record, value);
                return;
            }
        }

        base.SetValueAsObject(record, value);
    }

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Key, {this.Type.Name})";
}
