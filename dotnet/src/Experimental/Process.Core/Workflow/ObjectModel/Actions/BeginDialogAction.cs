// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class BeginDialogAction : ProcessAction<BeginDialog>
{
    public BeginDialogAction(BeginDialog source)
        : base(source)
    {
    }

    public override Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        // %%% TODO
        return Task.CompletedTask;
    }
}
