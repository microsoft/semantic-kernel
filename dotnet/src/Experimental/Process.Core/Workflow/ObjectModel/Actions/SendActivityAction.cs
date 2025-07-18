// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SendActivityAction : ProcessAction<SendActivity>
{
    private readonly ActivityNotificationHandler _handler;

    public SendActivityAction(SendActivity source, ActivityNotificationHandler handler)
        : base(source)
    {
        if (source.Activity is null)
        {
            throw new InvalidActionException($"{nameof(SendActivity)} action must have an activity defined.");
        }

        this._handler = handler;
    }

    protected override async Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        await this._handler.Invoke(this.Model.Activity!, context.Engine).ConfigureAwait(false);
    }
}
