// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.Extensions.Logging;
using Microsoft.PowerFx;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal sealed record class ProcessActionContext(RecalcEngine Engine, ProcessActionScopes Scopes, Kernel Kernel, ILogger Logger)
{
    private FoundryExpressionEngine? _expressionEngine;

    public FoundryExpressionEngine ExpressionEngine => this._expressionEngine ??= new FoundryExpressionEngine(this.Engine);
}

internal abstract class ProcessAction<TAction>(TAction model) : ProcessAction(model)
    where TAction : DialogAction
{
    public new TAction Model => (TAction)base.Model;
}

internal abstract class ProcessAction
{
    public const string RootActionId = "(root)";

    private string? _parentId;

    public string Id => this.Model.Id.Value;

    public string ParentId => this._parentId ??= this.Model.GetParentId() ?? RootActionId;

    public DialogAction Model { get; }

    protected ProcessAction(DialogAction model)
    {
        if (!model.HasRequiredProperties)
        {
            throw new InvalidActionException($"Action {this.GetType().Name} [{model.Id}]");
        }

        this.Model = model;
    }

    public async Task ExecuteAsync(ProcessActionContext context, CancellationToken cancellationToken)
    {
        cancellationToken.ThrowIfCancellationRequested();

        try
        {
            // Execute each action in the current context
            await this.HandleAsync(context, cancellationToken).ConfigureAwait(false);
        }
        catch (ProcessWorkflowException exception)
        {
            context.Logger.LogError(exception, "*** ACTION [{Id}] ERROR - {TypeName}\n{Message}", this.Id, this.GetType().Name, exception.Message);
            throw;
        }
        catch (Exception exception)
        {
            context.Logger.LogError(exception, "*** ACTION [{Id}] ERROR - {TypeName}\n{Message}", this.Id, this.GetType().Name, exception.Message);
            throw new ProcessWorkflowException($"Unexpected failure executing action #{this.Id} [{this.GetType().Name}]", exception);
        }
    }

    protected abstract Task HandleAsync(ProcessActionContext context, CancellationToken cancellationToken);
}
