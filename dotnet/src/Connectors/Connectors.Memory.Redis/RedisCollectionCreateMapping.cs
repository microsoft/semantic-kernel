// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using NRedisStack.Search;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains mapping helpers to use when creating a redis vector collection.
/// </summary>
internal static class RedisCollectionCreateMapping
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
    /// Map from the given list of <see cref="VectorStoreProperty"/> items to the Redis <see cref="Schema"/>.
    /// </summary>
    /// <param name="properties">The property definitions to map from.</param>
    /// <param name="useDollarPrefix">A value indicating whether to include $. prefix for field names as required in JSON mode.</param>
    /// <returns>The mapped Redis <see cref="Schema"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if there are missing required or unsupported configuration options set.</exception>
    public static Schema MapToSchema(IEnumerable<PropertyModel> properties, bool useDollarPrefix)
    {
        var schema = new Schema();
        var fieldNamePrefix = useDollarPrefix ? "$." : string.Empty;

        // Loop through all properties and create the index fields.
        foreach (var property in properties)
        {
            var storageName = property.StorageName;

            switch (property)
            {
                case KeyPropertyModel keyProperty:
                    // Do nothing, since key is not stored as part of the payload and therefore doesn't have to be added to the index.
                    continue;

                case DataPropertyModel dataProperty when dataProperty.IsIndexed || dataProperty.IsFullTextIndexed:
                    if (dataProperty.IsIndexed && dataProperty.IsFullTextIndexed)
                    {
                        throw new InvalidOperationException($"Property '{dataProperty.ModelName}' has both {nameof(VectorStoreDataProperty.IsIndexed)} and {nameof(VectorStoreDataProperty.IsFullTextIndexed)} set to true, and this is not supported by the Redis VectorStore.");
                    }

                    // Add full text search field index.
                    if (dataProperty.IsFullTextIndexed)
                    {
                        if (dataProperty.Type == typeof(string) || IsTagsType(dataProperty.Type))
                        {
                            schema.AddTextField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else
                        {
                            throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string or IEnumerable<string>. The Redis VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string or IEnumerable<string> properties only.");
                        }
                    }

                    // Add filter field index.
                    if (dataProperty.IsIndexed)
                    {
                        if (dataProperty.Type == typeof(string))
                        {
                            schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else if (IsTagsType(dataProperty.Type))
                        {
                            schema.AddTagField(new FieldName($"{fieldNamePrefix}{storageName}.*", storageName));
                        }
                        else if (RedisCollectionCreateMapping.s_supportedFilterableNumericDataTypes.Contains(dataProperty.Type))
                        {
                            schema.AddNumericField(new FieldName($"{fieldNamePrefix}{storageName}", storageName));
                        }
                        else
                        {
                            throw new InvalidOperationException($"Property '{dataProperty.ModelName}' is marked as {nameof(VectorStoreDataProperty.IsIndexed)}, but the property type '{dataProperty.Type}' is not supported. Only string, IEnumerable<string> and numeric properties are supported for filtering by the Redis VectorStore.");
                        }
                    }

                    continue;

                case VectorPropertyModel vectorProperty:
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

        static bool IsTagsType(Type type)
            => (type.IsArray && type.GetElementType() == typeof(string))
                || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>) && type.GenericTypeArguments[0] == typeof(string))
                || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(HashSet<>) && type.GenericTypeArguments[0] == typeof(string));
    }

    /// <summary>
    /// Get the configured <see cref="Schema.VectorField.VectorAlgo"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured the default is <see cref="Schema.VectorField.VectorAlgo.HNSW"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="Schema.VectorField.VectorAlgo"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a index type was chosen that isn't supported by Redis.</exception>
    public static Schema.VectorField.VectorAlgo GetSDKIndexKind(VectorPropertyModel vectorProperty)
        => vectorProperty.IndexKind switch
        {
            IndexKind.Hnsw or null => Schema.VectorField.VectorAlgo.HNSW,
            IndexKind.Flat => Schema.VectorField.VectorAlgo.FLAT,
            _ => throw new InvalidOperationException($"Index kind '{vectorProperty.IndexKind}' for {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };

    /// <summary>
    /// Get the configured distance metric from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is cosine.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen distance metric.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Redis.</exception>
    public static string GetSDKDistanceAlgorithm(VectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => "COSINE",
            DistanceFunction.CosineDistance => "COSINE",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanSquaredDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };

    /// <summary>
    /// Get the vector type to pass to the SDK based on the data type of the vector property.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The SDK required vector type.</returns>
    /// <exception cref="InvalidOperationException">Thrown if the property data type is not supported by the connector.</exception>
    public static string GetSDKVectorType(VectorPropertyModel vectorProperty)
        => (Nullable.GetUnderlyingType(vectorProperty.EmbeddingType) ?? vectorProperty.EmbeddingType) switch
        {
            Type t when t == typeof(ReadOnlyMemory<float>) => "FLOAT32",
            Type t when t == typeof(Embedding<float>) => "FLOAT32",
            Type t when t == typeof(float[]) => "FLOAT32",
            Type t when t == typeof(ReadOnlyMemory<double>) => "FLOAT64",
            Type t when t == typeof(Embedding<double>) => "FLOAT64",
            Type t when t == typeof(double[]) => "FLOAT64",

            null => throw new UnreachableException("null embedding type"),
            _ => throw new InvalidOperationException($"Vector data type '{vectorProperty.Type.Name}' for {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Redis VectorStore.")
        };
}
