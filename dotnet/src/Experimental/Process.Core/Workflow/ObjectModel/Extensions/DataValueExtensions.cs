// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class DataValueExtensions
{
    public static FormulaValue ToFormulaValue(this DataValue? value) =>
        value switch
        {
            null => FormulaValue.NewBlank(),
            StringDataValue stringValue => FormulaValue.New(stringValue.Value),
            NumberDataValue numberValue => FormulaValue.New(numberValue.Value),
            BooleanDataValue boolValue => FormulaValue.New(boolValue.Value),
            DateTimeDataValue dateTimeValue => FormulaValue.New(dateTimeValue.Value.DateTime),
            DateDataValue dateValue => FormulaValue.New(dateValue.Value),
            TimeDataValue timeValue => FormulaValue.New(timeValue.Value),
            //RecordDataValue recordValue => FormulaValue.NewRecordFromFields(recordValue.Properties), // %%% TODO
            //TableDataValue tableValue => FormulaValue.NewTable(), // %%% TODO
            _ => FormulaValue.NewError(new Microsoft.PowerFx.ExpressionError { Message = $"Unknown literal type: {value.GetType().Name}" }),
        };
}
