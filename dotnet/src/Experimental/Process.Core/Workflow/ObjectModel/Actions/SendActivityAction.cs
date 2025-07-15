// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SendActivityAction : ProcessAction<SendActivity>
{
    private readonly ProcessActionEnvironment _environment;

    public SendActivityAction(SendActivity source, ProcessActionEnvironment environment)
        : base(source)
    {
        if (source.Activity is null)
        {
            throw new InvalidActionException($"{nameof(SendActivity)} action must have an activity defined.");
        }

        this._environment = environment;
    }

    public override async Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        await this._environment.ActivityNotificationHandler(this.Action.Activity!, engine).ConfigureAwait(false); // %%% NULL OVERRIDE
    }
}
