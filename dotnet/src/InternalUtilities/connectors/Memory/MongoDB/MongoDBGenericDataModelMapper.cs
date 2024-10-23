// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within MongoDB.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class MongoDBGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, BsonDocument>
{
    /// <summary>A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</summary>
    private readonly VectorStoreRecordDefinition _vectorStoreRecordDefinition;

    /// <summary>
    /// Initializes a new instance of the <see cref="MongoDBGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="vectorStoreRecordDefinition">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    public MongoDBGenericDataModelMapper(VectorStoreRecordDefinition vectorStoreRecordDefinition)
    {
        Verify.NotNull(vectorStoreRecordDefinition);

        this._vectorStoreRecordDefinition = vectorStoreRecordDefinition;
    }

    /// <inheritdoc />
    public BsonDocument MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        Verify.NotNull(dataModel);

        var document = new BsonDocument();

        // Loop through all known properties and map each from the data model to the storage model.
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
        {
            var storagePropertyName = property.StoragePropertyName ?? property.DataModelPropertyName;

            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                document[MongoDBConstants.MongoReservedKeyPropertyName] = dataModel.Key;
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                if (dataModel.Data is not null && dataModel.Data.TryGetValue(dataProperty.DataModelPropertyName, out var dataValue))
                {
                    document[storagePropertyName] = BsonValue.Create(dataValue);
                }
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (dataModel.Vectors is not null && dataModel.Vectors.TryGetValue(vectorProperty.DataModelPropertyName, out var vectorValue))
                {
                    document[storagePropertyName] = BsonArray.Create(GetVectorArray(vectorValue));
                }
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
        foreach (var property in this._vectorStoreRecordDefinition.Properties)
        {
            var storagePropertyName = property.StoragePropertyName ?? property.DataModelPropertyName;

            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                if (storageModel.TryGetValue(MongoDBConstants.MongoReservedKeyPropertyName, out var keyValue))
                {
                    key = keyValue.AsString;
                }
            }
            else if (property is VectorStoreRecordDataProperty dataProperty)
            {
                if (!storageModel.TryGetValue(storagePropertyName, out var dataValue))
                {
                    continue;
                }

                dataProperties.Add(dataProperty.DataModelPropertyName, GetDataPropertyValue(property.DataModelPropertyName, property.PropertyType, dataValue));
            }
            else if (property is VectorStoreRecordVectorProperty vectorProperty && options.IncludeVectors)
            {
                if (!storageModel.TryGetValue(storagePropertyName, out var vectorValue))
                {
                    continue;
                }

                vectorProperties.Add(vectorProperty.DataModelPropertyName, GetVectorPropertyValue(property.DataModelPropertyName, property.PropertyType, vectorValue));
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
