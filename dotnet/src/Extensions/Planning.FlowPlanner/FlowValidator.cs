// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel.Diagnostics;

// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;

internal class FlowValidator : IFlowValidator
{
    public void Validate(Flow flow)
    {
        Verify.NotNullOrWhiteSpace(flow.Goal, nameof(flow.Goal));

        try
        {
            var sorted = flow.SortSteps();

            if (sorted.Count == 0)
            {
                throw new ArgumentException("Flow must contain at least one flow step.");
            }
        }
        catch (Exception ex)
        {
            throw new ArgumentException("Flow steps must be a partial order set.", ex);
        }
    }
}
