// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class EndConversationAction : ProcessAction<EndConversation> // %%% REMOVE ???
{
    public EndConversationAction(EndConversation model)
        : base(model)
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        return Task.CompletedTask;
    }
}
