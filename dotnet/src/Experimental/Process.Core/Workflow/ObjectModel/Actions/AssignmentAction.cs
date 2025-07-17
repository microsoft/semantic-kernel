// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal abstract class AssignmentAction<TAction> : ProcessAction<TAction> where TAction : DialogAction
{
    protected AssignmentAction(TAction model, Func<PropertyPath?> resolver)
        : base(model)
    {
        this.Target =
            resolver.Invoke() ??
            throw new InvalidActionException($"Action '{model.GetType().Name}' must have a variable path defined.");

        if (string.IsNullOrWhiteSpace(this.Target.VariableScopeName))
        {
            throw new InvalidActionException($"Action '{model.GetType().Name}' must define a variable scope.");
        }
        if (string.IsNullOrWhiteSpace(this.Target.VariableName))
        {
            throw new InvalidActionException($"Action '{model.GetType().Name}' must define a variable name.");
        }
    }

    public PropertyPath Target { get; }

    protected void AssignTarget(ProcessActionContext context, FormulaValue result)
    {
        context.Engine.SetScopedVariable(context.Scopes, ActionScopeType.Parse(this.Target.VariableScopeName), this.Target.VariableName!, result);
        string? resultValue = result.Format();
        string valuePosition = (resultValue?.IndexOf('\n') ?? -1) >= 0 ? Environment.NewLine : " ";
        Console.WriteLine( // %%% DEVTRACE
            $"""
            !!! ASSIGN {this.GetType().Name} [{this.Id}]
                NAME: {this.Target.Format()}
                VALUE:{valuePosition}{result.Format()} ({result.GetType().Name})
            """);
    }
}
