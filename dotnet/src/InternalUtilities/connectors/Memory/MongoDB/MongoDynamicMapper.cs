// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// A mapper that maps between the dynamic data model and the model that the data is stored under, within MongoDB.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class MongoDynamicMapper(CollectionModel model) : IMongoMapper<Dictionary<string, object?>>
{
    /// <inheritdoc />
    public BsonDocument MapFromDataToStorageModel(Dictionary<string, object?> dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        Verify.NotNull(dataModel);

        var document = new BsonDocument();

        document[MongoConstants.MongoReservedKeyPropertyName] = !dataModel.TryGetValue(model.KeyProperty.ModelName, out var keyValue)
            ? throw new InvalidOperationException($"Missing value for key property '{model.KeyProperty.ModelName}")
            : keyValue switch
            {
                string s => s,
                null => throw new InvalidOperationException($"Key property '{model.KeyProperty.ModelName}' is null."),
                _ => throw new InvalidCastException($"Key property '{model.KeyProperty.ModelName}' must be a string.")
            };

        document[MongoConstants.MongoReservedKeyPropertyName] = (string)(dataModel[model.KeyProperty.ModelName]
            ?? throw new InvalidOperationException($"Key property '{model.KeyProperty.ModelName}' is null."));

        foreach (var property in model.DataProperties)
        {
            if (dataModel.TryGetValue(property.ModelName, out var dataValue))
            {
                document[property.StorageName] = BsonValue.Create(dataValue);
            }
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            // Don't create a property if it doesn't exist in the dictionary
            if (dataModel.TryGetValue(property.ModelName, out var vectorValue))
            {
                var vector = generatedEmbeddings?[i]?[recordIndex] is Embedding ge
                    ? ge
                    : vectorValue;

                document[property.StorageName] = BsonArray.Create(
                    vector switch
                    {
                        ReadOnlyMemory<float> m
                            => MemoryMarshal.TryGetArray(m, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length ? segment.Array : m.ToArray(),
                        Embedding<float> e
                            => MemoryMarshal.TryGetArray(e.Vector, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length ? segment.Array : e.Vector.ToArray(),
                        float[] a => a,

                        null => Array.Empty<object>(),

                        _ => throw new UnreachableException()
                    });
            }
        }

        return document;
    }

    /// <inheritdoc />
    public Dictionary<string, object?> MapFromStorageToDataModel(BsonDocument storageModel, bool includeVectors)
    {
        Verify.NotNull(storageModel);

        var result = new Dictionary<string, object?>();

        // Loop through all known properties and map each from the storage model to the data model.
        foreach (var property in model.Properties)
        {
            switch (property)
            {
                case KeyPropertyModel keyProperty:
                    result[keyProperty.ModelName] = storageModel.TryGetValue(MongoConstants.MongoReservedKeyPropertyName, out var keyValue)
                        ? keyValue.AsString
                        : throw new InvalidOperationException("No key property was found in the record retrieved from storage.");
                    continue;

                case DataPropertyModel dataProperty:
                    if (storageModel.TryGetValue(dataProperty.StorageName, out var dataValue))
                    {
                        result.Add(dataProperty.ModelName, GetDataPropertyValue(property.ModelName, property.Type, dataValue));
                    }
                    continue;

                case VectorPropertyModel vectorProperty:
                    if (includeVectors && storageModel.TryGetValue(vectorProperty.StorageName, out var vectorValue))
                    {
                        result.Add(
                            vectorProperty.ModelName,
                            vectorValue.IsBsonNull
                                ? null
                                : (Nullable.GetUnderlyingType(property.Type) ?? property.Type) switch
                                {
                                    Type t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(vectorValue.AsBsonArray.Select(item => (float)item.AsDouble).ToArray()),
                                    Type t when t == typeof(Embedding<float>) => new Embedding<float>(vectorValue.AsBsonArray.Select(item => (float)item.AsDouble).ToArray()),
                                    Type t when t == typeof(float[]) => vectorValue.AsBsonArray.Select(item => (float)item.AsDouble).ToArray(),

                                    _ => throw new UnreachableException()
                                });
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

        var result = propertyType switch
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

            _ => (object?)null
        };

        if (result is not null)
        {
            return result;
        }

        if (propertyType.IsArray)
        {
            return propertyType switch
            {
                Type t when t == typeof(bool[]) => value.AsBsonArray.Select(x => x.AsBoolean).ToArray(),
                Type t when t == typeof(bool?[]) => value.AsBsonArray.Select(x => x.AsNullableBoolean).ToArray(),
                Type t when t == typeof(string[]) => value.AsBsonArray.Select(x => x.AsString).ToArray(),
                Type t when t == typeof(int[]) => value.AsBsonArray.Select(x => x.AsInt32).ToArray(),
                Type t when t == typeof(int?[]) => value.AsBsonArray.Select(x => x.AsNullableInt32).ToArray(),
                Type t when t == typeof(long[]) => value.AsBsonArray.Select(x => x.AsInt64).ToArray(),
                Type t when t == typeof(long?[]) => value.AsBsonArray.Select(x => x.AsNullableInt64).ToArray(),
                Type t when t == typeof(float[]) => value.AsBsonArray.Select(x => (float)x.AsDouble).ToArray(),
                Type t when t == typeof(float?[]) => value.AsBsonArray.Select(x => (float?)x.AsNullableDouble).ToArray(),
                Type t when t == typeof(double[]) => value.AsBsonArray.Select(x => x.AsDouble).ToArray(),
                Type t when t == typeof(double?[]) => value.AsBsonArray.Select(x => x.AsNullableDouble).ToArray(),
                Type t when t == typeof(decimal[]) => value.AsBsonArray.Select(x => x.AsDecimal).ToArray(),
                Type t when t == typeof(decimal?[]) => value.AsBsonArray.Select(x => x.AsNullableDecimal).ToArray(),
                Type t when t == typeof(DateTime[]) => value.AsBsonArray.Select(x => x.ToUniversalTime()).ToArray(),
                Type t when t == typeof(DateTime?[]) => value.AsBsonArray.Select(x => x.ToNullableUniversalTime()).ToArray(),

                _ => (object?)null
            };
        }

        if (propertyType.IsGenericType && propertyType.GetGenericTypeDefinition() == typeof(List<>))
        {
            return propertyType switch
            {
                Type t when t == typeof(List<bool>) => value.AsBsonArray.Select(x => x.AsBoolean).ToList(),
                Type t when t == typeof(List<bool?>) => value.AsBsonArray.Select(x => x.AsNullableBoolean).ToList(),
                Type t when t == typeof(List<string>) => value.AsBsonArray.Select(x => x.AsString).ToList(),
                Type t when t == typeof(List<int>) => value.AsBsonArray.Select(x => x.AsInt32).ToList(),
                Type t when t == typeof(List<int?>) => value.AsBsonArray.Select(x => x.AsNullableInt32).ToList(),
                Type t when t == typeof(List<long>) => value.AsBsonArray.Select(x => x.AsInt64).ToList(),
                Type t when t == typeof(List<long?>) => value.AsBsonArray.Select(x => x.AsNullableInt64).ToList(),
                Type t when t == typeof(List<float>) => value.AsBsonArray.Select(x => (float)x.AsDouble).ToList(),
                Type t when t == typeof(List<float?>) => value.AsBsonArray.Select(x => (float?)x.AsNullableDouble).ToList(),
                Type t when t == typeof(List<double>) => value.AsBsonArray.Select(x => x.AsDouble).ToList(),
                Type t when t == typeof(List<double?>) => value.AsBsonArray.Select(x => x.AsNullableDouble).ToList(),
                Type t when t == typeof(List<decimal>) => value.AsBsonArray.Select(x => x.AsDecimal).ToList(),
                Type t when t == typeof(List<decimal?>) => value.AsBsonArray.Select(x => x.AsNullableDecimal).ToList(),
                Type t when t == typeof(List<DateTime>) => value.AsBsonArray.Select(x => x.ToUniversalTime()).ToList(),
                Type t when t == typeof(List<DateTime?>) => value.AsBsonArray.Select(x => x.ToNullableUniversalTime()).ToList(),

                _ => (object?)null
            };
        }

        throw new NotSupportedException($"Mapping for property {propertyName} with type {propertyType.FullName} is not supported in dynamic data model.");
    }

    #endregion
}
