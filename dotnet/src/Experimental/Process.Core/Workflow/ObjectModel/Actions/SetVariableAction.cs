// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SetVariableAction : AssignmentAction<SetVariable>
{
    public SetVariableAction(SetVariable action)
        : base(action, () => action.Variable?.Path)
    {
        if (this.Action.Value is null)
        {
            throw new InvalidActionException($"{nameof(ParseValue)} must define {nameof(ParseValue.Value)}");
        }
    }

    public override Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        FormulaValue result = engine.EvaluateExpression(this.Action.Value!);

        if (result is ErrorValue errorVal) // %%% APPLY EVERYWHERE (OR CENTRAL)
        {
            throw new ProcessActionException($"Unable to evaluate expression.  Error: {errorVal.Errors[0].Message}");
        }

        this.AssignTarget(engine, scopes, result);

        return Task.CompletedTask;
    }
}
