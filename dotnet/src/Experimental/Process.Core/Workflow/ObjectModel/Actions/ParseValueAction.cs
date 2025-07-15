// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ParseValueAction : AssignmentAction<ParseValue>
{
    public ParseValueAction(ParseValue source)
        : base(source, () => source.Variable?.Path)
    {
        if (this.Action.Value is null)
        {
            throw new InvalidActionException($"{nameof(ParseValue)} must define {nameof(ParseValue.Value)}");
        }
    }

    public override Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        ValueExpression value = this.Action.Value!;
        DataType valueType = this.Action.ValueType!;

        FormulaValue result = engine.EvaluteExpression(value);

        FormulaValue? parsedResult = null;
        if (result is StringValue stringValue)
        {
            // %%% TODO: TRIM ```json ... ```
            if (valueType is RecordDataType recordType)
            {
                JsonDocument json = JsonDocument.Parse(stringValue.Value);
                JsonElement currentElement = json.RootElement;
                parsedResult = ParseRecord(currentElement, recordType);
            }
        }

        if (parsedResult is not null)
        {
            this.AssignTarget(engine, scopes, parsedResult);
        }
        // %%% ELSE THROW ???

        return Task.CompletedTask;
    }

    private static RecordValue ParseRecord(JsonElement currentElement, RecordDataType recordType)
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
                        BooleanDataType => BooleanValue.New(propertyElement.GetBoolean()),
                        NumberDataType => NumberValue.New(propertyElement.GetDecimal()),
                        RecordDataType => ParseRecord(propertyElement, (RecordDataType)property.Value.Type),
                        _ => throw new InvalidActionException($"Unsupported data type '{property.Value.Type}' for property '{property.Key}'") // %%% EXCEPTION TYPE & MESSAGE
                    };
                yield return new NamedValue(property.Key, parsedValue);
            }
        }
    }
}
