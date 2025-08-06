// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ParseValueAction : AssignmentAction<ParseValue>
{
    public ParseValueAction(ParseValue model)
        : base(model, Throw.IfNull(model.Variable?.Path, $"{nameof(model)}.{nameof(model.Variable)}.{nameof(InitializablePropertyPath.Path)}"))
    {
        if (this.Model.Value is null)
        {
            throw new InvalidActionException($"{nameof(ParseValue)} must define {nameof(ParseValue.Value)}");
        }
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        EvaluationResult<DataValue> result = context.ExpressionEngine.GetValue(this.Model.Value!, context.Scopes); // %%% FAILURE CASE (CATCH) & NULL OVERRIDE

        FormulaValue? parsedResult = null;

        if (result.Value is StringDataValue stringValue)
        {
            if (string.IsNullOrWhiteSpace(stringValue.Value))
            {
                parsedResult = FormulaValue.NewBlank();
            }
            else
            {
                parsedResult =
                    this.Model.ValueType switch
                    {
                        StringDataType => StringValue.New(stringValue.Value),
                        NumberDataType => NumberValue.New(stringValue.Value),
                        BooleanDataType => BooleanValue.New(stringValue.Value),
                        RecordDataType recordType => ParseRecord(recordType, stringValue.Value),
                        _ => null
                    };
            }
        }

        if (parsedResult is null)
        {
            throw new ProcessActionException($"Unable to parse {result.Value.GetType().Name}");
        }

        this.AssignTarget(context, parsedResult);

        return Task.CompletedTask;
    }

    private static RecordValue ParseRecord(RecordDataType recordType, string rawText)
    {
        string jsonText = rawText.TrimJsonDelimiter();
        JsonDocument json = JsonDocument.Parse(jsonText);
        JsonElement currentElement = json.RootElement;
        return recordType.ParseRecord(currentElement);
    }
}
