// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Bot.ObjectModel.Abstractions;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SetVariableAction : AssignmentAction<SetVariable>
{
    public SetVariableAction(SetVariable model)
        : base(model, Throw.IfNull(model.Variable?.Path, $"{nameof(model)}.{nameof(model.Variable)}.{nameof(InitializablePropertyPath.Path)}"))
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        if (this.Model.Value is null)
        {
            this.AssignTarget(context, FormulaValue.NewBlank());
        }
        else
        {
            EvaluationResult<DataValue> result = context.ExpressionEngine.GetValue(this.Model.Value, context.Scopes); // %%% FAILURE CASE (CATCH)

            this.AssignTarget(context, result.Value.ToFormulaValue());
        }

        return Task.CompletedTask;
    }
}
