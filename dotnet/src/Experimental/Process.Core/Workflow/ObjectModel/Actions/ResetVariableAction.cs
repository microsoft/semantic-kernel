// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ResetVariableAction : AssignmentAction<ResetVariable>
{
    public ResetVariableAction(ResetVariable model)
        : base(model, Throw.IfNull(model.Variable, $"{nameof(model)}.{nameof(model.Variable)}"))
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        context.Engine.ClearScopedVariable(context.Scopes, this.Target);
        Console.WriteLine( // %%% LOGGER
            $"""
            !!! CLEAR {this.GetType().Name} [{this.Id}]
                NAME: {this.Model.Variable!.Format()}
            """);

        return Task.CompletedTask;
    }
}
