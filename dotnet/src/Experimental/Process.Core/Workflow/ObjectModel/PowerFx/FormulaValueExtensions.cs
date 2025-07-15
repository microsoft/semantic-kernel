// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Linq;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal delegate object? GetFormulaValue(FormulaValue value);

internal static class FormulaValueExtensions
{
    private static readonly ImmutableDictionary<Type, GetFormulaValue> s_handlers =
        new Dictionary<Type, GetFormulaValue>()
        {
            { typeof(BooleanValue), FromBooleanValue },
            { typeof(DecimalValue), FromDecimalValue },
            { typeof(DateValue), FromDateTimeValue },
            { typeof(RecordValue), FromRecordValue },
            { typeof(StringValue), FromStringValue },
        }.ToImmutableDictionary();

    public static string? Format(this FormulaValue value)
    {
        Type valueType = value.GetType();

        if (s_handlers.TryGetValue(valueType, out GetFormulaValue? handler))
        {
            return $"{handler.Invoke(value) ?? "-"} ({valueType.Name})";
        }

        foreach (KeyValuePair<Type, GetFormulaValue> kvp in s_handlers)
        {
            if (kvp.Key.IsAssignableFrom(valueType))
            {
                return $"{kvp.Value.Invoke(value) ?? "-"} ({valueType.Name})";
            }
        }

        return value.ToString();
    }

    // %%% TODO
    //VoidValue
    //NamedValue
    //BlobValue
    //ErrorValue
    //ColorValue
    //NumberValue
    //TableValue
    //BlankValue
    //DateValue
    //GuidValue
    //TimeValue

    private static object? FromBooleanValue(FormulaValue value) => ((BooleanValue)value).Value;
    private static object? FromDecimalValue(FormulaValue value) => ((DecimalValue)value).Value;
    private static object? FromDateTimeValue(FormulaValue value) => ((DateValue)value).GetConvertedValue(TimeZoneInfo.Local);
    private static object? FromStringValue(FormulaValue value) => ((StringValue)value).Value;
    private static object? FromRecordValue(FormulaValue value) =>
        $"""
        [
        {string.Join(Environment.NewLine, ((RecordValue)value).Fields.Select(field => $"  {field.Name}={field.Value.Format()}"))}
        ]
        """;
}
