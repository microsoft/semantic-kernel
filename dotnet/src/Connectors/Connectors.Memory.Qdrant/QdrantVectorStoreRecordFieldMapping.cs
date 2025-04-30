// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Qdrant client sdk.
/// </summary>
internal static class QdrantVectorStoreRecordFieldMapping
{
    public static VectorStoreRecordModelBuildingOptions GetModelBuildOptions(bool hasNamedVectors)
        => new()
        {
            RequiresAtLeastOneVector = !hasNamedVectors,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = hasNamedVectors,

            SupportedKeyPropertyTypes = [typeof(ulong), typeof(Guid)],
            SupportedDataPropertyTypes = QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes,
            SupportedEnumerableDataPropertyElementTypes = QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes,
            SupportedVectorPropertyTypes = QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes
        };

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    public static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(DateTimeOffset)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    /// <remarks>
    /// While qdrant supports float32 and uint64, the api only supports float64, therefore
    /// any float32 vectors will be converted to float64 before being sent to qdrant.
    /// </remarks>
    public static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    /// <summary>
    /// Convert the given <paramref name="payloadValue"/> to the correct native type based on its properties.
    /// </summary>
    /// <param name="payloadValue">The value to convert to a native type.</param>
    /// <param name="targetType">The target type to convert the value to.</param>
    /// <returns>The converted native value.</returns>
    /// <exception cref="VectorStoreRecordMappingException">Thrown when an unsupported type is encountered.</exception>
    public static object? ConvertFromGrpcFieldValueToNativeType(Value payloadValue, Type targetType)
    {
        return payloadValue.KindCase switch
        {
            Value.KindOneofCase.NullValue => null,
            Value.KindOneofCase.IntegerValue =>
                targetType == typeof(int) || targetType == typeof(int?) ?
                (object)(int)payloadValue.IntegerValue :
                (object)payloadValue.IntegerValue,
            Value.KindOneofCase.StringValue =>
                ConvertStringValue(payloadValue.StringValue),
            Value.KindOneofCase.DoubleValue =>
                targetType == typeof(float) || targetType == typeof(float?) ?
                (object)(float)payloadValue.DoubleValue :
                (object)payloadValue.DoubleValue,
            Value.KindOneofCase.BoolValue => payloadValue.BoolValue,
            Value.KindOneofCase.ListValue => VectorStoreRecordMapping.CreateEnumerable(
                payloadValue.ListValue.Values.Select(
                    x => ConvertFromGrpcFieldValueToNativeType(x, VectorStoreRecordPropertyVerification.GetCollectionElementType(targetType))),
                targetType),
            _ => throw new VectorStoreRecordMappingException($"Unsupported grpc value kind {payloadValue.KindCase}."),
        };

        object ConvertStringValue(string stringValue)
        {
            return targetType switch
            {
                Type t when t == typeof(DateTimeOffset) || t == typeof(DateTimeOffset?) => DateTimeOffset.Parse(stringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind),
                _ => stringValue,
            };
        }
    }

    /// <summary>
    /// Convert the given <paramref name="sourceValue"/> to a <see cref="Value"/> object that can be stored in Qdrant.
    /// </summary>
    /// <param name="sourceValue">The object to convert.</param>
    /// <returns>The converted Qdrant value.</returns>
    /// <exception cref="VectorStoreRecordMappingException">Thrown when an unsupported type is encountered.</exception>
    public static Value ConvertToGrpcFieldValue(object? sourceValue)
    {
        var value = new Value();
        if (sourceValue is null)
        {
            value.NullValue = NullValue.NullValue;
        }
        else if (sourceValue is int intValue)
        {
            value.IntegerValue = intValue;
        }
        else if (sourceValue is long longValue)
        {
            value.IntegerValue = longValue;
        }
        else if (sourceValue is string stringValue)
        {
            value.StringValue = stringValue;
        }
        else if (sourceValue is float floatValue)
        {
            value.DoubleValue = floatValue;
        }
        else if (sourceValue is double doubleValue)
        {
            value.DoubleValue = doubleValue;
        }
        else if (sourceValue is bool boolValue)
        {
            value.BoolValue = boolValue;
        }
        else if (sourceValue is DateTimeOffset dateTimeOffsetValue)
        {
            value.StringValue = dateTimeOffsetValue.ToString("O");
        }
        else if (sourceValue is IEnumerable<int> ||
            sourceValue is IEnumerable<long> ||
            sourceValue is IEnumerable<string> ||
            sourceValue is IEnumerable<float> ||
            sourceValue is IEnumerable<double> ||
            sourceValue is IEnumerable<bool> ||
            sourceValue is IEnumerable<DateTime> ||
            sourceValue is IEnumerable<DateTimeOffset>)
        {
            var listValue = sourceValue as IEnumerable;
            value.ListValue = new ListValue();
            foreach (var item in listValue!)
            {
                value.ListValue.Values.Add(ConvertToGrpcFieldValue(item));
            }
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Unsupported source value type {sourceValue?.GetType().FullName}.");
        }

        return value;
    }
}
