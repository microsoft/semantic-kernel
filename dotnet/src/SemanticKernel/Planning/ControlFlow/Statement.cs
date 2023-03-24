// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public abstract class Statement
{
    protected Statement(ConditionGroup conditionGroup)
    {
        this.ConditionGroup = conditionGroup;
    }

    public ConditionGroup ConditionGroup { get; }

    public abstract bool Evaluate(SKContext context);
}
