// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ParseValueAction : AssignmentAction<ParseValue>
{
    public ParseValueAction(ParseValue source)
        : base(source, () => source.Variable?.Path)
    {
        if (this.Model.Value is null)
        {
            throw new InvalidActionException($"{nameof(ParseValue)} must define {nameof(ParseValue.Value)}");
        }
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        FormulaValue? parsedResult = null;

        DataType valueType = this.Model.ValueType!; // %%% NULL OVERRIDE
        FormulaValue result = context.Engine.EvaluateExpression(this.Model.Value);

        if (result is StringValue stringValue)
        {
            parsedResult =
                valueType switch
                {
                    StringDataType => stringValue,
                    NumberDataType => NumberValue.New(stringValue.Value),
                    BooleanDataType => BooleanValue.New(stringValue.Value),
                    RecordDataType recordType => ParseRecord(recordType, stringValue.Value),
                    _ => null
                };
        }

        if (parsedResult is null)
        {
            throw new ProcessActionException($"Unable to parse {valueType.GetType().Name}");
        }

        this.AssignTarget(context, parsedResult);

        return Task.CompletedTask;
    }

    private static RecordValue ParseRecord(RecordDataType recordType, string rawText)
    {
        string jsonText = rawText.TrimJsonDelimeter();
        JsonDocument json = JsonDocument.Parse(jsonText);
        JsonElement currentElement = json.RootElement;
        return recordType.ParseRecord(currentElement);
    }
}
