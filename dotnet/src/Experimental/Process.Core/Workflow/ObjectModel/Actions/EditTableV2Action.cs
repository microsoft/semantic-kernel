// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class EditTableV2Action : AssignmentAction<EditTableV2>
{
    public EditTableV2Action(EditTableV2 model)
        : base(model, Throw.IfNull(model.ItemsVariable?.Path, $"{nameof(model)}.{nameof(model.ItemsVariable)}.{nameof(InitializablePropertyPath.Path)}"))
    {
    }

    protected override async Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        FormulaValue table = context.Scopes.Get(this.Target.VariableName!, ActionScopeType.Parse(this.Target.VariableScopeName));
        TableValue tableValue = (TableValue)table;

        EditTableOperation? changeType = this.Model.ChangeType;
        if (changeType is AddItemOperation addItemOperation)
        {
            FormulaValue result = context.Engine.EvaluateExpression(addItemOperation.Value);
            RecordValue newRecord = BuildRecord(tableValue.Type.ToRecord(), result);
            await tableValue.AppendAsync(newRecord, cancellationToken).ConfigureAwait(false);
            this.AssignTarget(context, tableValue);
        }
        else if (changeType is ClearItemsOperation)
        {
            await tableValue.ClearAsync(cancellationToken).ConfigureAwait(false);
        }
        else if (changeType is RemoveItemOperation) // %%% SUPPORT
        {
        }
        else if (changeType is TakeFirstItemOperation) // %%% SUPPORT
        {
        }

        static RecordValue BuildRecord(RecordType recordType, FormulaValue value)
        {
            return FormulaValue.NewRecordFromFields(recordType, GetValues());

            IEnumerable<NamedValue> GetValues()
            {
                // %%% TODO: expression.StructuredRecordExpression.Properties ???
                foreach (NamedFormulaType fieldType in recordType.GetFieldTypes())
                {
                    if (value is RecordValue recordValue)
                    {
                        yield return new NamedValue(fieldType.Name, recordValue.GetField(fieldType.Name));
                    }
                    else
                    {
                        yield return new NamedValue(fieldType.Name, value);
                    }
                }
            }
        }
    }
}
