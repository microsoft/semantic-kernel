// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Pinecone client sdk.
/// </summary>
internal static class PineconeVectorStoreRecordFieldMapping
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    public static readonly HashSet<Type> s_supportedKeyTypes = [typeof(string)];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    public static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(string),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
    ];

    /// <summary>A set of types that enumerable data properties on the provided model may use as their element types.</summary>
    public static readonly HashSet<Type> s_supportedEnumerableDataElementTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    public static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

    public static object? ConvertFromMetadataValueToNativeType(MetadataValue metadataValue, Type targetType)
        => metadataValue.Inner switch
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
            decimal decimalValue => ConvertToNumericValue(decimalValue, targetType),
            MetadataValue[] array => VectorStoreRecordMapping.CreateEnumerable(array.Select(x => ConvertFromMetadataValueToNativeType(x, VectorStoreRecordPropertyVerification.GetCollectionElementType(targetType))), targetType),
            List<MetadataValue> list => VectorStoreRecordMapping.CreateEnumerable(list.Select(x => ConvertFromMetadataValueToNativeType(x, VectorStoreRecordPropertyVerification.GetCollectionElementType(targetType))), targetType),
            _ => throw new VectorStoreRecordMappingException($"Unsupported metadata type: '{metadataValue.Inner?.GetType().FullName}'."),
        };

    // TODO: take advantage of MetadataValue.TryCreate once we upgrade the version of Pinecone.NET
    public static MetadataValue ConvertToMetadataValue(object? sourceValue)
        => sourceValue switch
        {
            bool boolValue => boolValue,
            string stringValue => stringValue,
            int intValue => intValue,
            long longValue => longValue,
            float floatValue => floatValue,
            double doubleValue => doubleValue,
            decimal decimalValue => decimalValue,
            string[] stringArray => stringArray,
            List<string> stringList => stringList,
            IEnumerable<string> stringEnumerable => stringEnumerable.ToArray(),
            _ => throw new VectorStoreRecordMappingException($"Unsupported source value type '{sourceValue?.GetType().FullName}'.")
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
            _ => throw new VectorStoreRecordMappingException($"Unsupported target numeric type '{targetType.FullName}'."),
        };
    }
}
