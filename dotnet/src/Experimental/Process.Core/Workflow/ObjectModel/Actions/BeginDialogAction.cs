// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class BeginDialogAction : ProcessAction<BeginDialog>
{
    public BeginDialogAction(BeginDialog model)
        : base(model)
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        // %%% TODO
        return Task.CompletedTask;
    }
}
