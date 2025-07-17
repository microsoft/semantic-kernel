// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Pinecone client sdk.
/// </summary>
internal static class PineconeFieldMapping
{
    public static object? ConvertFromMetadataValueToNativeType(MetadataValue metadataValue, Type targetType)
        => metadataValue.Value switch
        {
            null => null,
            bool v => v,
            string v => v,

            // Numeric values are not always coming from the SDK in the desired type
            // that the data model requires, so we need to convert them.
            int v => ConvertToNumericValue(v, targetType),
            long v => ConvertToNumericValue(v, targetType),
            float v => ConvertToNumericValue(v, targetType),
            double v => ConvertToNumericValue(v, targetType),

            IEnumerable<MetadataValue> enumerable => DeserializeCollection(enumerable, targetType),

            _ => throw new InvalidOperationException($"Unsupported metadata type: '{metadataValue.Value?.GetType().FullName}'."),
        };

    private static object? DeserializeCollection(IEnumerable<MetadataValue> collection, Type targetType)
        => targetType switch
        {
            Type t when t == typeof(List<string>)
                => collection.Select(v => (string)v.Value).ToList(),
            Type t when t == typeof(string[])
                => collection.Select(v => (string)v.Value).ToArray(),

            _ => throw new UnreachableException($"Unsupported collection type {targetType.Name}"),
        };

    public static MetadataValue ConvertToMetadataValue(object? sourceValue)
        => sourceValue switch
        {
            bool boolValue => boolValue,
            bool[] bools => bools,
            List<bool> bools => bools,
            string stringValue => stringValue,
            string[] stringArray => stringArray,
            List<string> stringList => stringList,
            double doubleValue => doubleValue,
            double[] doubles => doubles,
            List<double> doubles => doubles,
            // Other numeric types are simply cast into double in implicit way.
            // We could consider supporting arrays of these types.
            int intValue => intValue,
            long longValue => longValue,
            float floatValue => floatValue,
            _ => throw new InvalidOperationException($"Unsupported source value type '{sourceValue?.GetType().FullName}'.")
        };

    private static object? ConvertToNumericValue(object? number, Type targetType)
        => number is null
            ? null
            : (Nullable.GetUnderlyingType(targetType) ?? targetType) switch
            {
                Type t when t == typeof(int) => (object)Convert.ToInt32(number),
                Type t when t == typeof(long) => Convert.ToInt64(number),
                Type t when t == typeof(float) => Convert.ToSingle(number),
                Type t when t == typeof(double) => Convert.ToDouble(number),

                _ => throw new InvalidOperationException($"Unsupported target numeric type '{targetType.FullName}'."),
            };
}
