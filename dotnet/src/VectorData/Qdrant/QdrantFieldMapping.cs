// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.Linq;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Qdrant client sdk.
/// </summary>
internal static class QdrantFieldMapping
{
    /// <summary>
    /// Convert the given <paramref name="payloadValue"/> to the correct native type based on its properties.
    /// </summary>
    /// <param name="payloadValue">The value to convert to a native type.</param>
    /// <param name="targetType">The target type to convert the value to.</param>
    /// <returns>The converted native value.</returns>
    /// <exception cref="InvalidOperationException">Thrown when an unsupported type is encountered.</exception>
    public static object? Deserialize(Value payloadValue, Type targetType)
    {
        if (Nullable.GetUnderlyingType(targetType) is Type unwrapped)
        {
            targetType = unwrapped;
        }

        return payloadValue.KindCase switch
        {
            Value.KindOneofCase.NullValue => null,

            Value.KindOneofCase.IntegerValue
                => targetType == typeof(int) ? (object)(int)payloadValue.IntegerValue : (object)payloadValue.IntegerValue,

            Value.KindOneofCase.StringValue when targetType == typeof(DateTimeOffset)
                => DateTimeOffset.Parse(payloadValue.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind),

            Value.KindOneofCase.StringValue when targetType == typeof(DateTime)
                => DateTime.Parse(payloadValue.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind),

#if NET
            Value.KindOneofCase.StringValue when targetType == typeof(DateOnly)
                => DateOnly.Parse(payloadValue.StringValue, CultureInfo.InvariantCulture),
#endif

            Value.KindOneofCase.StringValue
                => payloadValue.StringValue,

            Value.KindOneofCase.DoubleValue
                => targetType == typeof(float) ? (object)(float)payloadValue.DoubleValue : (object)payloadValue.DoubleValue,

            Value.KindOneofCase.BoolValue
                => payloadValue.BoolValue,

            Value.KindOneofCase.ListValue => DeserializeCollection(payloadValue, targetType),

            _ => throw new InvalidOperationException($"Unsupported grpc value kind {payloadValue.KindCase}."),
        };

        static object? DeserializeCollection(Value payloadValue, Type targetType)
            => targetType switch
            {
                Type t when t == typeof(List<int>)
                    => payloadValue.ListValue.Values.Select(v => (int)v.IntegerValue).ToList(),
                Type t when t == typeof(int[])
                    => payloadValue.ListValue.Values.Select(v => (int)v.IntegerValue).ToArray(),
                Type t when t == typeof(List<long>)
                    => payloadValue.ListValue.Values.Select(v => v.IntegerValue).ToList(),
                Type t when t == typeof(long[])
                    => payloadValue.ListValue.Values.Select(v => v.IntegerValue).ToArray(),

                Type t when t == typeof(List<string>)
                    => payloadValue.ListValue.Values.Select(v => v.StringValue).ToList(),
                Type t when t == typeof(string[])
                    => payloadValue.ListValue.Values.Select(v => v.StringValue).ToArray(),

                Type t when t == typeof(List<double>)
                    => payloadValue.ListValue.Values.Select(v => v.DoubleValue).ToList(),
                Type t when t == typeof(double[])
                    => payloadValue.ListValue.Values.Select(v => v.DoubleValue).ToArray(),
                Type t when t == typeof(List<float>)
                    => payloadValue.ListValue.Values.Select(v => (float)v.DoubleValue).ToList(),
                Type t when t == typeof(float[])
                    => payloadValue.ListValue.Values.Select(v => (float)v.DoubleValue).ToArray(),

                Type t when t == typeof(List<bool>)
                    => payloadValue.ListValue.Values.Select(v => v.BoolValue).ToList(),
                Type t when t == typeof(bool[])
                    => payloadValue.ListValue.Values.Select(v => v.BoolValue).ToArray(),

                Type t when t == typeof(List<DateTimeOffset>)
                    => payloadValue.ListValue.Values.Select(v => DateTimeOffset.Parse(v.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).ToList(),
                Type t when t == typeof(DateTimeOffset[])
                    => payloadValue.ListValue.Values.Select(v => DateTimeOffset.Parse(v.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).ToArray(),

                Type t when t == typeof(List<DateTime>)
                    => payloadValue.ListValue.Values.Select(v => DateTime.Parse(v.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).ToList(),
                Type t when t == typeof(DateTime[])
                    => payloadValue.ListValue.Values.Select(v => DateTime.Parse(v.StringValue, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind)).ToArray(),

#if NET
                Type t when t == typeof(List<DateOnly>)
                    => payloadValue.ListValue.Values.Select(v => DateOnly.Parse(v.StringValue, CultureInfo.InvariantCulture)).ToList(),
                Type t when t == typeof(DateOnly[])
                    => payloadValue.ListValue.Values.Select(v => DateOnly.Parse(v.StringValue, CultureInfo.InvariantCulture)).ToArray(),
#endif

                _ => throw new UnreachableException($"Unsupported collection type {targetType.Name}"),
            };
    }

    /// <summary>
    /// Convert the given <paramref name="sourceValue"/> to a <see cref="Value"/> object that can be stored in Qdrant.
    /// </summary>
    /// <param name="sourceValue">The object to convert.</param>
    /// <returns>The converted Qdrant value.</returns>
    /// <exception cref="InvalidOperationException">Thrown when an unsupported type is encountered.</exception>
    public static Value ConvertToGrpcFieldValue(object? sourceValue)
    {
        var value = new Value();
        switch (sourceValue)
        {
            case null:
                value.NullValue = NullValue.NullValue;
                break;
            case int intValue:
                value.IntegerValue = intValue;
                break;
            case long longValue:
                value.IntegerValue = longValue;
                break;
            case string stringValue:
                value.StringValue = stringValue;
                break;
            case float floatValue:
                value.DoubleValue = floatValue;
                break;
            case double doubleValue:
                value.DoubleValue = doubleValue;
                break;
            case bool boolValue:
                value.BoolValue = boolValue;
                break;
            case DateTimeOffset dateTimeOffsetValue:
                value.StringValue = dateTimeOffsetValue.ToString("O");
                break;
            case DateTime dateTimeValue:
                value.StringValue = dateTimeValue.ToString("O");
                break;
#if NET
            case DateOnly dateOnlyValue:
                value.StringValue = dateOnlyValue.ToString("O");
                break;
#endif
            case IEnumerable<int> or
                    IEnumerable<long> or
                    IEnumerable<string> or
                    IEnumerable<float> or
                    IEnumerable<double> or
                    IEnumerable<bool> or
                    IEnumerable<DateTime> or
                    IEnumerable<DateTimeOffset>:
            {
                var listValue = sourceValue as IEnumerable;
                value.ListValue = new ListValue();
                foreach (var item in listValue!)
                {
                    value.ListValue.Values.Add(ConvertToGrpcFieldValue(item));
                }

                break;
            }

            default:
                throw new InvalidOperationException($"Unsupported source value type {sourceValue?.GetType().FullName}.");
        }

        return value;
    }
}
