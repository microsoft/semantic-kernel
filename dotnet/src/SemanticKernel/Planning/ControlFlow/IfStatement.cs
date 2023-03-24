// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public sealed class IfStatement : Statement
{
    public IfStatement(ConditionGroup conditionGroup, string thenXml, string? elseXml = null)
        : base(conditionGroup)
    {
        this.ThenPlan = thenXml;
        this.ElsePlan = elseXml;
    }

    public string ThenPlan { get; set; }
    public string? ElsePlan { get; set; }

    public override bool Evaluate(SKContext context)
    {
        throw new NotImplementedException();
    }
}
