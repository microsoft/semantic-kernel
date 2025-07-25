// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.Immutable;
using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflow.ObjectModel.Validation;

internal sealed class ProcessValidationWalker : BotElementWalker
{
    private readonly List<ValidationFailure> _failures;

    public ProcessValidationWalker(BotElement rootElement)
    {
        this._failures = [];
        this.Visit(rootElement);
        this.Failures = this._failures.ToImmutableArray();
    }

    public bool IsValid => this.Failures.Length == 0;

    public ImmutableArray<ValidationFailure> Failures { get; }

    public override bool DefaultVisit(BotElement definition)
    {
        Console.WriteLine($"> {definition.GetType().Name}");
        if (definition is UnknownBotElement)
        {
            this._failures.Add(new ElementValidationFailure(definition, "Unknown element"));
        }
        else if (definition is UnknownDialogAction unknownAction)
        {
            this._failures.Add(new ActionValidationFailure(unknownAction, "Unknown action"));
        }
        else if (definition is DialogAction action)
        {
            if (!action.HasRequiredProperties)
            {
                this._failures.Add(new ActionValidationFailure(action, "Missing required properties"));
            }
        }

        return true;
    }
}
