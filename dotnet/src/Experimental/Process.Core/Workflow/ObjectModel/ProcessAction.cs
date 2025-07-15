// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal abstract class ProcessAction<TAction>(TAction action) : ProcessAction(action) where TAction : DialogAction
{
    public new TAction Action => action;
}

internal abstract class ProcessAction(DialogAction action)
{
    public ActionId Id => action.Id;

    public DialogAction Action => action;

    public abstract Task HandleAsync(KernelProcessStepContext context, ProcessActionScopes scopes, RecalcEngine engine, Kernel kernel, CancellationToken cancellationToken);
}

internal abstract class AssignmentAction<TAction> : ProcessAction<TAction> where TAction : DialogAction
{
    protected AssignmentAction(TAction action, Func<PropertyPath?> resolver)
        : base(action)
    {
        this.Target =
            resolver.Invoke() ??
            throw new InvalidActionException($"Action '{action.GetType().Name}' must have a variable path defined.");

        if (string.IsNullOrWhiteSpace(this.Target.VariableScopeName))
        {
            throw new InvalidActionException($"Action '{action.GetType().Name}' must define a variable scope.");
        }
        if (string.IsNullOrWhiteSpace(this.Target.VariableName))
        {
            throw new InvalidActionException($"Action '{action.GetType().Name}' must define a variable name.");
        }
    }

    public PropertyPath Target { get; }

    protected void AssignTarget(RecalcEngine engine, ProcessActionScopes scopes, FormulaValue result)
    {
        engine.SetScopedVariable(scopes, this.Target.VariableScopeName!, this.Target.VariableName!, result);
        string? resultValue = result.Format();
        string valuePosition = (resultValue?.IndexOf('\n') ?? -1) >= 0 ? Environment.NewLine : " ";
        Console.WriteLine( // %%% DEVTRACE
            $"""
            !!! ASSIGN {this.GetType().Name} [{this.Id}]
                NAME: {this.Target.VariableScopeName}.{this.Target.VariableName}
                VALUE:{valuePosition}{result.Format()}
            """);
    }
}
