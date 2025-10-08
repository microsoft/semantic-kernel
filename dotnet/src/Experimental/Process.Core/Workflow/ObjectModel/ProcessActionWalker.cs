// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Bot.ObjectModel;

namespace Microsoft.SemanticKernel.Process.Workflows;

internal sealed class ProcessActionWalker : BotElementWalker
{
    private readonly ProcessActionVisitor _visitor;

    public ProcessActionWalker(BotElement rootElement, ProcessActionVisitor visitor)
    {
        this._visitor = visitor;
        this.Visit(rootElement);
        this._visitor.Complete();
    }

    public override bool DefaultVisit(BotElement definition)
    {
        if (definition is DialogAction action)
        {
            action.Accept(this._visitor);
        }

        return true;
    }
}
