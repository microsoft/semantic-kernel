// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Plan result after execution.
/// </summary>
public class PlanResult : FunctionResult
{
    /// <summary>
    /// Results from all steps in plan.
    /// </summary>
    public IReadOnlyCollection<PlanResult> StepResults { get; internal set; } = Array.Empty<PlanResult>();

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    public PlanResult(string functionName, string pluginName, SKContext context)
        : base(functionName, pluginName, context)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PlanResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="value">Function result object.</param>
    public PlanResult(string functionName, string pluginName, SKContext context, object? value)
        : base(functionName, pluginName, context, value)
    {
    }
}
