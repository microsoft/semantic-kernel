// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.VectorData;
using NRedisStack.Search;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains mapping helpers to use when creating a redis vector collection.
/// </summary>
internal static class RedisVectorStoreCollectionCreateMapping
{
    /// <summary>A set of number types that are supported for filtering.</summary>
    public static readonly HashSet<Type> s_supportedFilterableNumericDataTypes =
    [
        typeof(short),
        typeof(sbyte),
        typeof(byte),
        typeof(ushort),
        typeof(int),
        typeof(uint),
        typeof(long),
        typeof(ulong),
        typeof(float),
        typeof(double),
        typeof(decimal),

        typeof(short?),
        typeof(sbyte?),
        typeof(byte?),
        typeof(ushort?),
        typeof(int?),
        typeof(uint?),
        typeof(long?),
        typeof(ulong?),
        typeof(float?),
        typeof(double?),
        typeof(decimal?),
    ];

    /// <summary>
    /// Map from the given list of <see cref="VectorStoreRecordProperty"/> items to the Redis <see cref="Schema"/>.
    /// </summary>
    /// <param name="properties">The property definitions to map from.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name that should be used when serializing it to json for data and vector properties.</param>
    /// <param name="useDollarPrefix">A value indicating whether to include $. prefix for field names as required in JSON mode.</param>
    /// <returns>The mapped Redis <see cref="Schema"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if there are missing required or unsupported configuration options set.</exception>
    public static Schema MapToSchema(IEnumerable<VectorStoreRecordProperty> properties, IReadOnlyDictionary<string, string> storagePropertyNames, bool useDollarPrefix)
    {
        var schema = new Schema();
        var fieldNamePrefix = useDollarPrefix ? "$." : string.Empty;

        // Loop through all properties and create the index fields.
        foreach (var property in properties)
        {
            // Key property.
            if (property is VectorStoreRecordKeyProperty keyProperty)
            {
                // Do nothing, since key is not stored as part of the payload and therefore doesn't have to be added to the index.
                continue;
            }

            // Data property.
            if (property is VectorStoreRecordDataProperty dataProperty && (dataProperty.IsIndexed || dataProperty.IsFullTextSearchable))
            {
                var storageName = storagePropertyNames[dataProperty.DataModelPropertyName];

                if (dataProperty.IsIndexed && dataProperty.IsFullTextSearchable)
                {
                    throw new InvalidOperationException($"Property '{dataProperty.DataModelPropertyName}' has both {nameof(VectorStoreRecordDataProperty.IsIndexed)} and {nameof(VectorStoreRecordDataProperty.IsFullTextSearchable)} set to true, and this is not supported by the Redis VectorStore.");
                }

                // Add full text search field index.
                if (dataProperty.IsFullTextSearchable)
                {
                    if (dataProperty.PropertyType == typeof(string) || (typeof(IEnumerable).IsAssignableFrom(dataProperty.PropertyType) && GetEnumerableType(dataProperty.PropertyType) == typeof(string)))
                    {
                        schema.AddTextField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                    }
                    else
                    {
                        throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextSearchable)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.DataModelPropertyName}' is set to true, but the property type is not a string or IEnumerable<string>. The Redis VectorStore supports {nameof(dataProperty.IsFullTextSearchable)} on string or IEnumerable<string> properties only.");
                    }
                }

                // Add filter field index.
                if (dataProperty.IsIndexed)
                {
                    if (dataProperty.PropertyType == typeof(string))
                    {
                        schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                    }
                    else if (typeof(IEnumerable).IsAssignableFrom(dataProperty.PropertyType) && GetEnumerableType(dataProperty.PropertyType) == typeof(string))
                    {
                        schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}.*", storageName));
                    }
                    else if (RedisVectorStoreCollectionCreateMapping.s_supportedFilterableNumericDataTypes.Contains(dataProperty.PropertyType))
                    {
                        schema.AddNumericField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                    }
                    else
                    {
                        throw new InvalidOperationException($"Property '{dataProperty.DataModelPropertyName}' is marked as {nameof(VectorStoreRecordDataProperty.IsIndexed)}, but the property type '{dataProperty.PropertyType}' is not supported. Only string, IEnumerable<string> and numeric properties are supported for filtering by the Redis VectorStore.");
                    }
                }

                continue;
            }

            // Vector property.
            if (property is VectorStoreRecordVectorProperty vectorProperty)
            {
                if (vectorProperty.Dimensions is not > 0)
                {
                    throw new InvalidOperationException($"Property {nameof(vectorProperty.Dimensions)} on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' must be set to a positive integer to create a collection.");
                }

                var storageName = storagePropertyNames[vectorProperty.DataModelPropertyName];
                var indexKind = GetSDKIndexKind(vectorProperty);
                var vectorType = GetSDKVectorType(vectorProperty);
                var dimensions = vectorProperty.Dimensions.Value.ToString(CultureInfo.InvariantCulture);
                var distanceAlgorithm = GetSDKDistanceAlgorithm(vectorProperty);
                schema.AddVectorField(new FieldName($"{fieldNamePrefix}{storageName}", storageName), indexKind, new Dictionary<string, object>()
                {
                    ["TYPE"] = vectorType,
                    ["DIM"] = dimensions,
                    ["DISTANCE_METRIC"] = distanceAlgorithm
                });
            }
        }

        return schema;
    }

    /// <summary>
    /// Get the configured <see cref="Schema.VectorField.VectorAlgo"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured the default is <see cref="Schema.VectorField.VectorAlgo.HNSW"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="Schema.VectorField.VectorAlgo"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a index type was chosen that isn't supported by Redis.</exception>
    public static Schema.VectorField.VectorAlgo GetSDKIndexKind(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.IndexKind is null)
        {
            return Schema.VectorField.VectorAlgo.HNSW;
        }

        return vectorProperty.IndexKind switch
        {
            IndexKind.Hnsw => Schema.VectorField.VectorAlgo.HNSW,
            IndexKind.Flat => Schema.VectorField.VectorAlgo.FLAT,
            _ => throw new InvalidOperationException($"Index kind '{vectorProperty.IndexKind}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Redis VectorStore.")
        };
    }

    /// <summary>
    /// Get the configured distance metric from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is cosine.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen distance metric.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Redis.</exception>
    public static string GetSDKDistanceAlgorithm(VectorStoreRecordVectorProperty vectorProperty)
    {
        if (vectorProperty.DistanceFunction is null)
        {
            return "COSINE";
        }

        return vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity => "COSINE",
            DistanceFunction.CosineDistance => "COSINE",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanSquaredDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Redis VectorStore.")
        };
    }

    /// <summary>
    /// Get the vector type to pass to the SDK based on the data type of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The SDK required vector type.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property data type is not supported by the connector.</exception>
    public static string GetSDKVectorType(VectorStoreRecordVectorProperty vectorProperty)
    {
        return vectorProperty.PropertyType switch
        {
            Type t when t == typeof(ReadOnlyMemory<float>) => "FLOAT32",
            Type t when t == typeof(ReadOnlyMemory<float>?) => "FLOAT32",
            Type t when t == typeof(ReadOnlyMemory<double>) => "FLOAT64",
            Type t when t == typeof(ReadOnlyMemory<double>?) => "FLOAT64",
            _ => throw new InvalidOperationException($"Vector data type '{vectorProperty.PropertyType.FullName}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.DataModelPropertyName}' is not supported by the Redis VectorStore.")
        };
    }

    /// <summary>
    /// Gets the type of object stored in the given enumerable type.
    /// </summary>
    /// <param name="type">The enumerable to get the stored type for.</param>
    /// <returns>The type of object stored in the given enumerable type.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the given type is not enumerable.</exception>
    private static Type GetEnumerableType(Type type)
    {
        if (type is IEnumerable)
        {
            return typeof(object);
        }
        else if (type.IsArray)
        {
            return type.GetElementType()!;
        }

        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(IEnumerable<>))
        {
            return type.GetGenericArguments()[0];
        }

        if (type.GetInterfaces().FirstOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>)) is Type enumerableInterface)
        {
            return enumerableInterface.GetGenericArguments()[0];
        }

        throw new InvalidOperationException($"Data type '{type}' for {nameof(VectorStoreRecordDataProperty)} is not supported by the Redis VectorStore.");
    }
}
