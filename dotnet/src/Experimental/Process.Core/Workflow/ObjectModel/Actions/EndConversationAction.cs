// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class EndConversationAction : ProcessAction<EndConversation>
{
    public EndConversationAction(EndConversation source)
        : base(source)
    {
    }

    public override Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }
}
