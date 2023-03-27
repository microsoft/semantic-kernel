// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.ControlFlow;

public sealed class EqualsCondition : Condition
{
    public override string Type => "Equals";
    public Dictionary<string, object> ExpectedVariableValue { get; }
    public EqualsCondition(string variable, string value)
    {
        this.ExpectedVariableValue = new Dictionary<string, object>() { { variable, value } };
    }

    public override bool Evaluate(SKContext context)
    {
        var isExactMatch = true;

        foreach (var (variableName, expectedExactValue) in this.ExpectedVariableValue)
        {
            if (context.Variables.ContainsKey(variableName))
            {
                isExactMatch = context.Variables[variableName].Equals(expectedExactValue);
            }
            else
            {
                // If the variable to check does not exists in the context, evaluates to false.
                isExactMatch = false;
            }

            if (!isExactMatch)
            {
                // If any of the provided variables are not exact match, don't need to check further.
                break;
            }
        }

        return isExactMatch;
    }
}
