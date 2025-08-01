// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ClearAllVariablesAction : ProcessAction<ClearAllVariables>
{
    public ClearAllVariablesAction(ClearAllVariables source)
        : base(source)
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        DataValue literalValue = this.Model.Variables.GetLiteralValue(); // %%% DON'T USE GetLiteralValue

        context.Engine.ClearScope(context.Scopes, ActionScopeType.Topic); // %%% EVALUATE "Variables"

        return Task.CompletedTask;
    }
}
