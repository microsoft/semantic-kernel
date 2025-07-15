// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ConditionGroupAction : ProcessAction<ConditionGroup>
{
    public ConditionGroupAction(ConditionGroup source)
        : base(source)
    {
    }

    public override Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        // %%% REMOVE
        //foreach (ConditionItem condition in this.Action.Conditions)
        //{
        //    if (engine.Eval(condition.Condition?.ExpressionText ?? "true").AsBoolean())
        //    {
        //        // %%% VERIFY IF ONLY ONE CONDITION IS EXPECTED / ALLOWED

        //    }
        //}
        return Task.CompletedTask;
    }
}
