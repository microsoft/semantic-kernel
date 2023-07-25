// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Flow;
using Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// A planner that execute plan in iterative way
/// </summary>
public class FlowPlanner
{
    private readonly KernelBuilder _kernelBuilder;

    private readonly IFlowStatusProvider _flowStatusProvider;

    private readonly Dictionary<object, string?> _globalSkillCollection;

    private readonly IFlowValidator _flowValidator;

    private readonly FlowPlannerConfig? _config;

    /// <summary>
    /// Initialize a new instance of the <see cref="FlowPlanner"/> class.
    /// </summary>
    /// <param name="kernelBuilder">The semantic kernel builder.</param>
    /// <param name="flowStatusProvider">The flow status provider.</param>
    /// <param name="globalSkillCollection">The global skill collection</param>
    /// <param name="validator">The flow validator.</param>
    /// <param name="config">Optional configuration object</param>
    public FlowPlanner(
        KernelBuilder kernelBuilder,
        IFlowStatusProvider flowStatusProvider,
        Dictionary<object, string?>? globalSkillCollection = null,
        IFlowValidator? validator = null,
        FlowPlannerConfig? config = null)
    {
        Verify.NotNull(kernelBuilder);

        this._kernelBuilder = kernelBuilder;
        this._flowStatusProvider = flowStatusProvider;
        this._globalSkillCollection = globalSkillCollection ?? new Dictionary<object, string?>();
        this._flowValidator = validator ?? new FlowValidator();
        this._config = config;
    }

    /// <summary>
    /// Plan and execute for the given goal
    ///
    /// </summary>
    /// <param name="flow">goal to achieve</param>
    /// <param name="sessionId">execution session id</param>
    /// <param name="input">current input</param>
    /// <returns>SKContext, which includes a json array of strings as output. The flow result is also exposed through the context when completes.</returns>
    [SKFunction]
    [SKName("ExecuteFlow")]
    [Description("Execute a flow")]
    public async Task<SKContext> ExecuteFlowAsync(
        [Description("The flow to execute")] Flow.Flow flow,
        [Description("Execution session id")] string sessionId,
        [Description("Current input")] string input)
    {
        try
        {
            this._flowValidator.Validate(flow);
        }
        catch (Exception ex)
        {
            throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Invalid flow", ex);
        }

        FlowExecutor executor = new(this._kernelBuilder, this._flowStatusProvider, this._globalSkillCollection, this._config);
        return await executor.ExecuteAsync(flow, sessionId, input).ConfigureAwait(false);
    }
}
