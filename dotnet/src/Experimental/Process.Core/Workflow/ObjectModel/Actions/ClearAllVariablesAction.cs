// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class ClearAllVariablesAction : ProcessAction<ClearAllVariables>
{
    public ClearAllVariablesAction(ClearAllVariables source)
        : base(source)
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        DataValue literalValue = this.Model.Variables.GetLiteralValue();

        if (literalValue is RecordDataValue recordValue)
        {
            //recordValue.Properties; // %%% TODO ?!?!!?!
        }

        return Task.CompletedTask;
    }
}
