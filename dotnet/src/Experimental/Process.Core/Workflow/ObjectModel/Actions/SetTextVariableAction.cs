// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SetTextVariableAction : AssignmentAction<SetTextVariable>
{
    public SetTextVariableAction(SetTextVariable model)
        : base(model, () => model.Variable?.Path)
    {
        if (this.Model.Value is null)
        {
            throw new InvalidActionException($"{nameof(SetTextVariable)} must define {nameof(SetTextVariable.Value)}");
        }
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        FormulaValue result = FormulaValue.New(context.Engine.Format(this.Model.Value));

        this.AssignTarget(context, result);

        return Task.CompletedTask;
    }
}
