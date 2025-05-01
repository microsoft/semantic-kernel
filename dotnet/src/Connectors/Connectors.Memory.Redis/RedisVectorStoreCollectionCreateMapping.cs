// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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
    /// <param name="useDollarPrefix">A value indicating whether to include $. prefix for field names as required in JSON mode.</param>
    /// <returns>The mapped Redis <see cref="Schema"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if there are missing required or unsupported configuration options set.</exception>
    public static Schema MapToSchema(IEnumerable<VectorStoreRecordPropertyModel> properties, bool useDollarPrefix)
    {
        var schema = new Schema();
        var fieldNamePrefix = useDollarPrefix ? "$." : string.Empty;

        // Loop through all properties and create the index fields.
        foreach (var property in properties)
        {
            var storageName = property.StorageName;

            switch (property)
            {
                case VectorStoreRecordKeyPropertyModel keyProperty:
                    // Do nothing, since key is not stored as part of the payload and therefore doesn't have to be added to the index.
                    continue;

                case VectorStoreRecordDataPropertyModel dataProperty when dataProperty.IsIndexed || dataProperty.IsFullTextIndexed:
                    if (dataProperty.IsIndexed && dataProperty.IsFullTextIndexed)
                    {
                        throw new InvalidOperationException($"Property '{dataProperty.ModelName}' has both {nameof(VectorStoreRecordDataProperty.IsIndexed)} and {nameof(VectorStoreRecordDataProperty.IsFullTextIndexed)} set to true, and this is not supported by the Redis VectorStore.");
                    }

                    // Add full text search field index.
                    if (dataProperty.IsFullTextIndexed)
                    {
                        if (dataProperty.Type == typeof(string) || (typeof(IEnumerable).IsAssignableFrom(dataProperty.Type) && GetEnumerableType(dataProperty.Type) == typeof(string)))
                        {
                            schema.AddTextField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else
                        {
                            throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string or IEnumerable<string>. The Redis VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string or IEnumerable<string> properties only.");
                        }
                    }

                    // Add filter field index.
                    if (dataProperty.IsIndexed)
                    {
                        if (dataProperty.Type == typeof(string))
                        {
                            schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else if (typeof(IEnumerable).IsAssignableFrom(dataProperty.Type) && GetEnumerableType(dataProperty.Type) == typeof(string))
                        {
                            schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}.*", storageName));
                        }
                        else if (RedisVectorStoreCollectionCreateMapping.s_supportedFilterableNumericDataTypes.Contains(dataProperty.Type))
                        {
                            schema.AddNumericField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else
                        {
                            throw new InvalidOperationException($"Property '{dataProperty.ModelName}' is marked as {nameof(VectorStoreRecordDataProperty.IsIndexed)}, but the property type '{dataProperty.Type}' is not supported. Only string, IEnumerable<string> and numeric properties are supported for filtering by the Redis VectorStore.");
                        }
                    }

                    continue;

                case VectorStoreRecordVectorPropertyModel vectorProperty:
                    var indexKind = GetSDKIndexKind(vectorProperty);
                    var vectorType = GetSDKVectorType(vectorProperty);
                    var dimensions = vectorProperty.Dimensions.ToString(CultureInfo.InvariantCulture);
                    var distanceAlgorithm = GetSDKDistanceAlgorithm(vectorProperty);
                    schema.AddVectorField(new FieldName($"{fieldNamePrefix}{storageName}", storageName), indexKind, new Dictionary<string, object>()
                    {
                        ["TYPE"] = vectorType,
                        ["DIM"] = dimensions,
                        ["DISTANCE_METRIC"] = distanceAlgorithm
                    });
                    continue;
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
    public static Schema.VectorField.VectorAlgo GetSDKIndexKind(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.IndexKind switch
        {
            IndexKind.Hnsw or null => Schema.VectorField.VectorAlgo.HNSW,
            IndexKind.Flat => Schema.VectorField.VectorAlgo.FLAT,
            _ => throw new InvalidOperationException($"Index kind '{vectorProperty.IndexKind}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };

    /// <summary>
    /// Get the configured distance metric from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is cosine.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen distance metric.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Redis.</exception>
    public static string GetSDKDistanceAlgorithm(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => "COSINE",
            DistanceFunction.CosineDistance => "COSINE",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanSquaredDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };

    /// <summary>
    /// Get the vector type to pass to the SDK based on the data type of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The SDK required vector type.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property data type is not supported by the connector.</exception>
    public static string GetSDKVectorType(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.EmbeddingType switch
        {
            Type t when t == typeof(ReadOnlyMemory<float>) => "FLOAT32",
            Type t when t == typeof(ReadOnlyMemory<float>?) => "FLOAT32",
            Type t when t == typeof(ReadOnlyMemory<double>) => "FLOAT64",
            Type t when t == typeof(ReadOnlyMemory<double>?) => "FLOAT64",
            null => throw new UnreachableException("null embedding type"),
            _ => throw new InvalidOperationException($"Vector data type '{vectorProperty.Type.Name}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };

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
