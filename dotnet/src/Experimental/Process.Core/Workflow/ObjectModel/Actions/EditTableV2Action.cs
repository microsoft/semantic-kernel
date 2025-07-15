// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class EditTableV2Action : AssignmentAction<EditTableV2>
{
    public EditTableV2Action(EditTableV2 source)
        : base(source, () => source.ItemsVariable?.Path)
    {
    }

    public override async Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        FormulaValue table = scopes[this.Target.VariableScopeName!][this.Target.VariableName!];  // %%% NULL OVERRIDE & MAKE UTILITY
        TableValue tableValue = (TableValue)table;

        EditTableOperation? changeType = this.Action.ChangeType;
        if (changeType is AddItemOperation addItemOperation)
        {
            FormulaValue result = engine.EvaluteExpression(addItemOperation.Value);
            RecordValue newRecord = BuildRecord(tableValue.Type.ToRecord(), result);
            await tableValue.AppendAsync(newRecord, cancellationToken).ConfigureAwait(false);
            this.AssignTarget(engine, scopes, tableValue);
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
                // %%% expression.StructuredRecordExpression.Properties ???
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
                    // %%% REMOVE ???
                    //if (fieldType.Type is StringType)
                    //{
                    //    // For string fields, we can use a placeholder value
                    //    yield return new NamedValue(fieldType.Name, value); // %%% TODO: VALUE
                    //    continue;
                    //}
                    //if (fieldType.Type is BooleanType)
                    //{
                    //    // For boolean fields, we can use a default boolean value
                    //    yield return new NamedValue(fieldType.Name, BooleanValue.New(true)); // %%% TODO: VALUE
                    //    continue;
                    //}
                    //if (fieldType.Type is DecimalType)
                    //{
                    //    // For number fields, we can use a default numeric value
                    //    yield return new NamedValue(fieldType.Name, NumberValue.New(-123)); // %%% TODO: VALUE
                    //}
                }
            }
        }
    }
}
