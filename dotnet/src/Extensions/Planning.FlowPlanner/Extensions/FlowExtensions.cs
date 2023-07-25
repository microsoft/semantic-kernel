// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130 // Namespace does not match folder structure
// ReSharper disable once CheckNamespace
namespace Microsoft.SemanticKernel.Planning.Flow;
#pragma warning restore IDE0130 // Namespace does not match folder structure

using System.Collections.Generic;
using System.Linq;

internal static class FlowExtensions
{
    internal static List<FlowStep> SortSteps(this Flow flow)
    {
        var sortedSteps = new List<FlowStep>();
        var remainingSteps = new List<FlowStep>(flow.Steps);

        while (remainingSteps.Count > 0)
        {
            var independentSteps = remainingSteps.Where(step => !remainingSteps.Any(step.DependsOn)).ToList();

            if (independentSteps.Count == 0)
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan,
                    "The plan contains circular dependencies.");
            }

            sortedSteps.AddRange(independentSteps);
            remainingSteps.RemoveAll(step => independentSteps.Contains(step));
        }

        return sortedSteps;
    }
}
