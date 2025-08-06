// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using System.Drawing;
using System.Linq;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using BlankType = Microsoft.PowerFx.Types.BlankType;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal delegate object? GetFormulaValue(FormulaValue value);

internal static class FormulaValueExtensions
{
    public static DataValue GetDataValue(this FormulaValue value) =>
        value switch
        {
            BooleanValue booleanValue => booleanValue.ToDataValue(),
            DecimalValue decimalValue => decimalValue.ToDataValue(),
            NumberValue numberValue => numberValue.ToDataValue(),
            DateValue dateValue => dateValue.ToDataValue(),
            DateTimeValue datetimeValue => datetimeValue.ToDataValue(),
            TimeValue timeValue => timeValue.ToDataValue(),
            StringValue stringValue => stringValue.ToDataValue(),
            GuidValue guidValue => guidValue.ToDataValue(),  // %%% CORRECT ???
            BlankValue blankValue => blankValue.ToDataValue(),
            VoidValue voidValue => voidValue.ToDataValue(),
            TableValue tableValue => tableValue.ToDataValue(),
            RecordValue recordValue => recordValue.ToDataValue(),
            //BlobValue // %%% DataValue ???
            //ErrorValue // %%% DataValue ???
            _ => throw new NotSupportedException($"Unsupported FormulaValue type: {value.GetType().Name}"),
        };

    public static DataType GetDataType(this FormulaValue value) =>
        value.Type switch
        {
            null => DataType.Blank,
            BooleanType => DataType.Boolean,
            DecimalType => DataType.Number,
            NumberType => DataType.Float,
            DateType => DataType.Date,
            DateTimeType => DataType.DateTime,
            TimeType => DataType.Time,
            StringType => DataType.String,
            GuidType => DataType.String,
            BlankType => DataType.String,
            RecordType => DataType.EmptyRecord,
            //BlobValue // %%% DataType ???
            //ErrorValue // %%% DataType ???
            UnknownType => DataType.Unspecified,
            _ => DataType.Unspecified,
        };

    public static string? Format(this FormulaValue value) =>
        value switch
        {
            BooleanValue booleanValue => $"{booleanValue.Value}",
            DecimalValue decimalValue => $"{decimalValue.Value}",
            NumberValue numberValue => $"{numberValue.Value}",
            DateValue dateValue => $"{dateValue.GetConvertedValue(TimeZoneInfo.Utc)}",
            DateTimeValue datetimeValue => $"{datetimeValue.GetConvertedValue(TimeZoneInfo.Utc)}",
            TimeValue timeValue => $"{timeValue.Value}",
            StringValue stringValue => $"{stringValue.Value}",
            GuidValue guidValue => $"{guidValue.Value}",
            BlankValue blankValue => string.Empty,
            VoidValue voidValue => string.Empty,
            TableValue tableValue => tableValue.ToString(), // %%% WORK ???
            RecordValue recordValue => recordValue.ToString(),
            //BlobValue // %%% DataValue ???
            //ErrorValue // %%% DataValue ???
            _ => throw new NotSupportedException($"Unsupported FormulaValue type: {value.GetType().Name}"),
        };

    // %%% TODO: Type conversion

    public static BooleanDataValue ToDataValue(this BooleanValue value) => BooleanDataValue.Create(value.Value);
    public static NumberDataValue ToDataValue(this DecimalValue value) => NumberDataValue.Create(value.Value);
    public static FloatDataValue ToDataValue(this NumberValue value) => FloatDataValue.Create(value.Value);
    public static DateTimeDataValue ToDataValue(this DateTimeValue value) => DateTimeDataValue.Create(value.GetConvertedValue(TimeZoneInfo.Utc));
    public static DateDataValue ToDataValue(this DateValue value) => DateDataValue.Create(value.GetConvertedValue(TimeZoneInfo.Utc));
    public static TimeDataValue ToDataValue(this TimeValue value) => TimeDataValue.Create(value.Value);
    public static StringDataValue ToDataValue(this StringValue value) => StringDataValue.Create(value.Value);
    public static StringDataValue ToDataValue(this GuidValue value) => StringDataValue.Create(value.Value.ToString("N")); // %%% FORMAT ???
    public static DataValue ToDataValue(this BlankValue _) => BlankDataValue.Blank();
    public static DataValue ToDataValue(this VoidValue _) => BlankDataValue.Blank(); // %%% CORRECT ???
    public static StringDataValue ToDataValue(this ColorValue value) => StringDataValue.Create(Enum.GetName(typeof(Color), value.Value)!); // %%% CORRECT ???

    public static TableDataValue ToDataValue(this TableValue value) =>
        TableDataValue.TableFromRecords(value.Rows.Select(row => row.Value.ToDataValue()).ToImmutableArray());

    public static RecordDataValue ToDataValue(this RecordValue value) =>
        RecordDataValue.RecordFromFields(value.Fields.Select(field => field.GetKeyValuePair()).ToImmutableArray());

    private static KeyValuePair<string, DataValue> GetKeyValuePair(this NamedValue value) => new(value.Name, value.Value.GetDataValue());
}
