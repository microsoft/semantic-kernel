// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Extension methods for <see cref="KernelResult"/> with plan execution results.
/// </summary>
public static class KernelResultPlanExtensions
{
    /// <summary>
    /// Returns plan execution results from <see cref="KernelResult"/>.
    /// </summary>
    /// <param name="kernelResult">Instance of <see cref="KernelResult"/>.</param>
    public static IReadOnlyCollection<PlanResult> GetPlanResults(this KernelResult kernelResult)
    {
        var functionResult = kernelResult.FunctionResults.FirstOrDefault();

        if (functionResult is not null && functionResult is PlanResult planResult)
        {
            return planResult.StepResults;
        }

        return Array.Empty<PlanResult>();
    }
}
