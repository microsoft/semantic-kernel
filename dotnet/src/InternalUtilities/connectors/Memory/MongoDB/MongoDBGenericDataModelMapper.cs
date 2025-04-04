// Copyright (c) Microsoft. All rights reserved.

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
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within MongoDB.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class MongoDBGenericDataModelMapper(VectorStoreRecordModel model) : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, BsonDocument>
{
    /// <inheritdoc />
    public BsonDocument MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        Verify.NotNull(dataModel);

        var document = new BsonDocument();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    document[MongoDBConstants.MongoReservedKeyPropertyName] = dataModel.Key;
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (dataModel.Data is not null && dataModel.Data.TryGetValue(dataProperty.ModelName, out var dataValue))
                    {
                        document[dataProperty.StorageName] = BsonValue.Create(dataValue);
                    }
                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(vectorProperty.ModelName, out var vectorValue))
                    {
                        document[property.StorageName] = BsonArray.Create(GetVectorArray(vectorValue));
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        return document;
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel(BsonDocument storageModel, StorageToDataModelMapperOptions options)
    {
        Verify.NotNull(storageModel);

        // Create variables to store the response properties.
        string? key = null;
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    if (storageModel.TryGetValue(MongoDBConstants.MongoReservedKeyPropertyName, out var keyValue))
                    {
                        key = keyValue.AsString;
                    }
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty:
                    if (storageModel.TryGetValue(dataProperty.StorageName, out var dataValue))
                    {
                        dataProperties.Add(dataProperty.ModelName, GetDataPropertyValue(property.ModelName, property.Type, dataValue));
                    }
                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    if (storageModel.TryGetValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        vectorProperties.Add(vectorProperty.ModelName, GetVectorPropertyValue(property.ModelName, property.Type, vectorValue));
                    }
                    continue;

                default:
                    throw new UnreachableException();
            }
        }

        if (key is null)
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        return new VectorStoreGenericDataModel<string>(key) { Data = dataProperties, Vectors = vectorProperties };
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
            _ => throw new NotSupportedException($"Mapping for property {propertyName} with type {propertyType.FullName} is not supported in generic data model.")
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
            _ => throw new NotSupportedException($"Mapping for property {propertyName} with type {propertyType.FullName} is not supported in generic data model.")
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
            _ => throw new NotSupportedException($"Mapping for type {vector.GetType().FullName} is not supported in generic data model.")
        };
    }

    #endregion
}
