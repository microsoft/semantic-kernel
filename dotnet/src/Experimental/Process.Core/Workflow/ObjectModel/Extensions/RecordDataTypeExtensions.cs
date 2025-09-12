// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class RecordDataTypeExtensions
{
    public static RecordValue ParseRecord(this RecordDataType recordType, JsonElement currentElement)
    {
        return FormulaValue.NewRecordFromFields(ParseValues());

        IEnumerable<NamedValue> ParseValues()
        {
            foreach (KeyValuePair<string, PropertyInfo> property in recordType.Properties)
            {
                JsonElement propertyElement = currentElement.GetProperty(property.Key);
                FormulaValue? parsedValue =
                    property.Value.Type switch
                    {
                        StringDataType => StringValue.New(propertyElement.GetString()),
                        NumberDataType => NumberValue.New(propertyElement.GetDecimal()),
                        BooleanDataType => BooleanValue.New(propertyElement.GetBoolean()),
                        DateTimeDataType dateTimeType => DateTimeValue.New(propertyElement.GetDateTime()),
                        DateDataType dateType => DateValue.New(propertyElement.GetDateTime()),
                        TimeDataType timeType => TimeValue.New(propertyElement.GetDateTimeOffset().TimeOfDay),
                        RecordDataType recordType => recordType.ParseRecord(propertyElement),
                        //TableDataValue tableValue => // %%% SUPPORT
                        _ => throw new UnknownDataTypeException($"Unsupported data type '{property.Value.Type}' for property '{property.Key}'")
                    };
                yield return new NamedValue(property.Key, parsedValue);
            }
        }
    }
}
