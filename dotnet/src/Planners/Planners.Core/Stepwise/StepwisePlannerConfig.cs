// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SemanticFunctions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

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
    public Func<string, string, ISKFunction?>? GetPluginFunction { get; set; }

    #endregion Use these to completely override the functions available for planning

    #region Execution configuration

    /// <summary>
    /// The maximum total number of tokens to allow in a completion request,
    /// which includes the tokens from the prompt and completion
    /// </summary>
    /// <remarks>
    /// Default value is 4000.
    /// </remarks>
    public int MaxTokens { get; set; } = 4000;

    /// <summary>
    /// The ratio of tokens to allocate to the completion request. (prompt / (prompt + completion))
    /// </summary>
    public double MaxTokensRatio { get; set; } = 0.1;

    internal int MaxCompletionTokens { get { return (int)(this.MaxTokens * this.MaxTokensRatio); } }

    internal int MaxPromptTokens { get { return (int)(this.MaxTokens * (1 - this.MaxTokensRatio)); } }

    /// <summary>
    /// The maximum number of iterations to allow in a plan.
    /// </summary>
    public int MaxIterations { get; set; } = 15;

    /// <summary>
    /// The minimum time to wait between iterations in milliseconds.
    /// </summary>
    public int MinIterationTimeMs { get; set; } = 0;

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
