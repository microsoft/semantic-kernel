// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ConditionGroupAction : ProcessAction<ConditionGroup>
{
    public ConditionGroupAction(ConditionGroup model)
        : base(model)
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
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
