// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class BotElementExtensions
{
    public static FormulaValue ToFormulaValue(this DataValue? value) =>
        value switch
        {
            null => FormulaValue.NewBlank(),
            BlankDataValue blankValue => BlankValue.NewBlank(),
            BooleanDataValue boolValue => FormulaValue.New(boolValue.Value),
            NumberDataValue numberValue => FormulaValue.New(numberValue.Value),
            FloatDataValue floatValue => FormulaValue.New(floatValue.Value),
            StringDataValue stringValue => FormulaValue.New(stringValue.Value),
            DateTimeDataValue dateTimeValue => FormulaValue.New(dateTimeValue.Value.DateTime),
            DateDataValue dateValue => FormulaValue.NewDateOnly(dateValue.Value),
            TimeDataValue timeValue => FormulaValue.New(timeValue.Value),
            TableDataValue tableValue => FormulaValue.NewTable(ParseRecordType(tableValue.Values.First()), tableValue.Values.Select(value => value.ToRecordValue())), // %%% TODO: RecordType
            RecordDataValue recordValue => recordValue.ToRecordValue(),
            //FileDataValue // %%% SUPPORT ???
            //OptionDataValue // %%% SUPPORT - Enum ???
            _ => FormulaValue.NewError(new Microsoft.PowerFx.ExpressionError { Message = $"Unknown literal type: {value.GetType().Name}" }),
        };

    public static FormulaType ToFormulaType(this DataType? type) =>
        type switch
        {
            null => FormulaType.Blank,
            BooleanDataType => FormulaType.Boolean,
            NumberDataType => FormulaType.Number,
            FloatDataType => FormulaType.Decimal,
            StringDataType => FormulaType.String,
            DateTimeDataType => FormulaType.DateTime,
            DateDataType => FormulaType.Date,
            TimeDataType => FormulaType.Time,
            //TableDataType => new TableType(), %%% ELEMENT TYPE
            RecordDataType => RecordType.Empty(),
            //FileDataType // %%% SUPPORT ???
            //OptionDataType // %%% SUPPORT - Enum ???
            DataType dataType => FormulaType.Blank, // %%% HANDLE ??? (FALLTHROUGH???)            
            //_ => FormulaType.Unknown,
        };

    public static RecordValue ToRecordValue(this RecordDataValue recordDataValue) =>
        FormulaValue.NewRecordFromFields(
            recordDataValue.Properties.Select(
                property => new NamedValue(property.Key, property.Value.ToFormulaValue())));

    private static RecordType ParseRecordType(RecordDataValue record)
    {
        RecordType recordType = RecordType.Empty();
        foreach (KeyValuePair<string, DataValue> property in record.Properties)
        {
            recordType.Add(property.Key, property.Value.GetDataType().ToFormulaType());
        }
        return recordType;
    }
}
