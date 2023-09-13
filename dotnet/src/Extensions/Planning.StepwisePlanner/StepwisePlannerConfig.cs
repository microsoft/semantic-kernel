// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.SemanticFunctions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.Stepwise;

/// <summary>
/// Configuration for Stepwise planner instances.
/// </summary>
public sealed class StepwisePlannerConfig : PlannerConfigBase
{
    #region Use these to configure which functions to include/exclude
    /// <summary>
    /// A list of functions to include in the plan creation request.
    /// </summary>
    public HashSet<string> IncludedFunctions { get; } = new();
    #endregion Use these to configure which functions to include/exclude

    #region Use these to completely override the functions available for planning

    /// <summary>
    /// Optional callback to get the available functions for planning.
    /// </summary>
    public Func<StepwisePlannerConfig, string?, CancellationToken, Task<IOrderedEnumerable<FunctionView>>>? GetAvailableFunctionsAsync { get; set; }

    /// <summary>
    /// Optional callback to get a function by name.
    /// </summary>
    public Func<string, string, ISKFunction?>? GetSkillFunction { get; set; }

    #endregion Use these to completely override the functions available for planning

    #region Execution configuration

    /// <summary>
    /// The maximum number of tokens to allow in a request and for completion.
    /// </summary>
    /// <remarks>
    /// Default value is 2000.
    /// </remarks>
    public int MaxTokens { get; set; } = 2000;

    /// <summary>
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    public int MaxIterations { get; set; } = 15;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; } = 0;

    /// <summary>
    /// Delegate to get the prompt template string.
    /// </summary>
    public Func<string>? GetPromptTemplate { get; set; } = null;

    /// <summary>
    /// The configuration to use for the prompt template.
    /// </summary>
    public PromptTemplateConfig? PromptUserConfig { get; set; } = null;

    /// <summary>
    /// A suffix to use within the default prompt template.
    /// </summary>
    public string Suffix { get; set; } = @"Let's break down the problem step by step and think about the best approach. Label steps as they are taken.

Continue the thought process!";

    #endregion Execution configuration
}
