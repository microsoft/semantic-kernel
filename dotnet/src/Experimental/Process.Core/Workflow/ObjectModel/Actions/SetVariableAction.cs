// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SetVariableAction : AssignmentAction<SetVariable>
{
    public SetVariableAction(SetVariable model)
        : base(model, () => model.Variable?.Path)
    {
        if (this.Model.Value is null)
        {
            throw new InvalidActionException($"{nameof(SetVariable)} must define {nameof(SetVariable.Value)}");
        }
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        FormulaValue result = context.Engine.EvaluateExpression(this.Model.Value).ThrowIfError();

        this.AssignTarget(context, result);

        return Task.CompletedTask;
    }
}
