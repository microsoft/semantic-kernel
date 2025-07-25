// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal sealed class SetTextVariableAction : AssignmentAction<SetTextVariable>
{
    public SetTextVariableAction(SetTextVariable model)
        : base(model, Throw.IfNull(model.Variable?.Path, $"{nameof(model)}.{nameof(model.Variable)}.{nameof(InitializablePropertyPath.Path)}"))
    {
    }

    protected override Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        FormulaValue result = FormulaValue.New(context.Engine.Format(this.Model.Value));

        this.AssignTarget(context, result);

        return Task.CompletedTask;
    }
}
