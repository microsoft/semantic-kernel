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
            bool boolValue => boolValue,
            string stringValue => stringValue,
            // Numeric values are not always coming from the SDK in the desired type
            // that the data model requires, so we need to convert them.
            int intValue => ConvertToNumericValue(intValue, targetType),
            long longValue => ConvertToNumericValue(longValue, targetType),
            float floatValue => ConvertToNumericValue(floatValue, targetType),
            double doubleValue => ConvertToNumericValue(doubleValue, targetType),
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
    {
        if (number is null)
        {
            return null;
        }

        return targetType switch
        {
            Type intType when intType == typeof(int) || intType == typeof(int?) => Convert.ToInt32(number),
            Type longType when longType == typeof(long) || longType == typeof(long?) => Convert.ToInt64(number),
            Type floatType when floatType == typeof(float) || floatType == typeof(float?) => Convert.ToSingle(number),
            Type doubleType when doubleType == typeof(double) || doubleType == typeof(double?) => Convert.ToDouble(number),
            Type decimalType when decimalType == typeof(decimal) || decimalType == typeof(decimal?) => Convert.ToDecimal(number),
            _ => throw new InvalidOperationException($"Unsupported target numeric type '{targetType.FullName}'."),
        };
    }
}
