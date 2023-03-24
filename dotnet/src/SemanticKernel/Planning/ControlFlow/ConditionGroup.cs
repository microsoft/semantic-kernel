// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public sealed class ConditionGroup
{
    public ICollection<Condition> Conditions { get; }
    public ICollection<ConditionGroup> ConditionGroups { get; }

    public ConditionGroup()
    {
        this.Conditions = new List<Condition>();
        this.ConditionGroups = new List<ConditionGroup>();
    }

    public bool Evaluate(SKContext context)
    {
        if (this.Conditions.Count == 0)
        {
            throw new InvalidOperationException("A condition group must have only one condition.");
        }
        if (this.ConditionGroups.Count > 1)
        {
            throw new NotSupportedException("A condition group with multiple conditions is not supported yet.");
        }

        return this.Conditions.Single().Evaluate(context);
    }
}
