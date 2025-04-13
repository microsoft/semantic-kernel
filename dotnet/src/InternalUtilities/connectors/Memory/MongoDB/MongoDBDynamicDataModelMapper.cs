﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// A mapper that maps between the dynamic data model and the model that the data is stored under, within MongoDB.
/// </summary>
[ExcludeFromCodeCoverage]
#pragma warning disable CS0618 // IVectorStoreRecordMapper is obsolete
internal sealed class MongoDBDynamicDataModelMapper(VectorStoreRecordModel model) : IMongoDBMapper<Dictionary<string, object?>>
#pragma warning restore CS0618
{
    /// <inheritdoc />
    public BsonDocument MapFromDataToStorageModel(Dictionary<string, object?> dataModel)
    {
        Verify.NotNull(dataModel);

        var document = new BsonDocument();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    document[MongoDBConstants.MongoReservedKeyPropertyName] = (string)(dataModel[keyProperty.ModelName]
                        ?? throw new InvalidOperationException($"Key property '{keyProperty.ModelName}' is null."));
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (dataModel.TryGetValue(dataProperty.ModelName, out var dataValue))
                    {
                        document[dataProperty.StorageName] = BsonValue.Create(dataValue);
                    }
                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (dataModel.TryGetValue(vectorProperty.ModelName, out var vectorValue))
                    {
                        document[vectorProperty.StorageName] = BsonArray.Create(GetVectorArray(vectorValue));
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return document;
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = storageModel.TryGetValue(MongoDBConstants.MongoReservedKeyPropertyName, out var keyValue)
                        ? keyValue.AsString
                        : throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (storageModel.TryGetValue(dataProperty.StorageName, out var dataValue))
                    {
                        result.Add(dataProperty.ModelName, GetDataPropertyValue(property.ModelName, property.Type, dataValue));
                    }
                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (storageModel.TryGetValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        result.Add(vectorProperty.ModelName, GetVectorPropertyValue(property.ModelName, property.Type, vectorValue));
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return result;
    }

    #region private

    private static object? GetDataPropertyValue(string propertyName, Type propertyType, BsonValue value)
    {
        if (value.IsBsonNull)
        {
            return null;
        }

        return propertyType switch
        {
            Type t when t == typeof(bool) => value.AsBoolean,
            Type t when t == typeof(bool?) => value.AsNullableBoolean,
            Type t when t == typeof(string) => value.AsString,
            Type t when t == typeof(int) => value.AsInt32,
            Type t when t == typeof(int?) => value.AsNullableInt32,
            Type t when t == typeof(long) => value.AsInt64,
            Type t when t == typeof(long?) => value.AsNullableInt64,
            Type t when t == typeof(float) => ((float)value.AsDouble),
            Type t when t == typeof(float?) => ((float?)value.AsNullableDouble),
            Type t when t == typeof(double) => value.AsDouble,
            Type t when t == typeof(double?) => value.AsNullableDouble,
            Type t when t == typeof(decimal) => value.AsDecimal,
            Type t when t == typeof(decimal?) => value.AsNullableDecimal,
            Type t when t == typeof(DateTime) => value.ToUniversalTime(),
            Type t when t == typeof(DateTime?) => value.ToNullableUniversalTime(),
            Type t when typeof(IEnumerable).IsAssignableFrom(t) => value.AsBsonArray.Select(
                item => GetDataPropertyValue(propertyName, VectorStoreRecordPropertyVerification.GetCollectionElementType(t), item)),
            _ => throw new NotSupportedException($"Mapping for property {propertyName} with type {propertyType.FullName} is not supported in dynamic data model.")
        };
    }

    private static object? GetVectorPropertyValue(string propertyName, Type propertyType, BsonValue value)
    {
        if (value.IsBsonNull)
        {
            return null;
        }

        return propertyType switch
        {
            Type t when t == typeof(ReadOnlyMemory<float>) || t == typeof(ReadOnlyMemory<float>?) =>
                new ReadOnlyMemory<float>(value.AsBsonArray.Select(item => (float)item.AsDouble).ToArray()),
            Type t when t == typeof(ReadOnlyMemory<double>) || t == typeof(ReadOnlyMemory<double>?) =>
                new ReadOnlyMemory<double>(value.AsBsonArray.Select(item => item.AsDouble).ToArray()),
            _ => throw new NotSupportedException($"Mapping for property {propertyName} with type {propertyType.FullName} is not supported in dynamic data model.")
        };
    }

    private static object GetVectorArray(object? vector)
    {
        if (vector is null)
        {
            return Array.Empty<object>();
        }

        return vector switch
        {
            ReadOnlyMemory<float> memoryFloat => memoryFloat.ToArray(),
            ReadOnlyMemory<double> memoryDouble => memoryDouble.ToArray(),
            _ => throw new NotSupportedException($"Mapping for type {vector.GetType().FullName} is not supported in dynamic data model.")
        };
    }

    #endregion
}
