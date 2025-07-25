// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Bot.ObjectModel;
using Microsoft.PowerFx.Types;
using Microsoft.SemanticKernel.Process.Workflows.Extensions;
using Microsoft.SemanticKernel.Process.Workflows.PowerFx;

namespace Microsoft.SemanticKernel.Process.Workflows.Actions;

internal abstract class AssignmentAction<TAction> : ProcessAction<TAction> where TAction : DialogAction
{
    protected AssignmentAction(TAction model, PropertyPath assignmentTarget)
        : base(model)
    {
        this.Target = assignmentTarget;
    }

    public PropertyPath Target { get; }

    protected void AssignTarget(ProcessActionContext context, FormulaValue result)
    {
        context.Engine.SetScopedVariable(context.Scopes, this.Target, result);
        string? resultValue = result.Format();
        string valuePosition = (resultValue?.IndexOf('\n') ?? -1) >= 0 ? Environment.NewLine : " ";
        Console.WriteLine( // %%% LOGGER
            $"""
            !!! ASSIGN {this.GetType().Name} [{this.Id}]
                NAME: {this.Target.Format()}
                VALUE:{valuePosition}{result.Format()} ({result.GetType().Name})
            """);
    }
}
