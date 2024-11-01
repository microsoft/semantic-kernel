﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Experimental.Orchestration.Abstractions;
using Microsoft.SemanticKernel.Experimental.Orchestration.Execution;

namespace Microsoft.SemanticKernel.Experimental.Orchestration;

/// <summary>
/// A flow orchestrator that using semantic kernel for execution.
/// </summary>
public class FlowOrchestrator
{
    private readonly IKernelBuilder _kernelBuilder;

    private readonly IFlowStatusProvider _flowStatusProvider;

    private readonly Dictionary<object, string?> _globalPluginCollection;

    private readonly IFlowValidator _flowValidator;

    private readonly FlowOrchestratorConfig? _config;

    /// <summary>
    /// Initialize a new instance of the <see cref="FlowOrchestrator"/> class.
    /// </summary>
    /// <param name="kernelBuilder">The semantic kernel builder.</param>
    /// <param name="flowStatusProvider">The flow status provider.</param>
    /// <param name="globalPluginCollection">The global plugin collection</param>
    /// <param name="validator">The flow validator.</param>
    /// <param name="config">Optional configuration object</param>
    public FlowOrchestrator(
        IKernelBuilder kernelBuilder,
        IFlowStatusProvider flowStatusProvider,
        Dictionary<object, string?>? globalPluginCollection = null,
        IFlowValidator? validator = null,
        FlowOrchestratorConfig? config = null)
    {
        Verify.NotNull(kernelBuilder);

        this._kernelBuilder = kernelBuilder;
        this._flowStatusProvider = flowStatusProvider;
        this._globalPluginCollection = globalPluginCollection ?? [];
        this._flowValidator = validator ?? new FlowValidator();
        this._config = config;
    }

    /// <summary>
    /// Execute a given flow.
    /// </summary>
    /// <param name="flow">goal to achieve</param>
    /// <param name="sessionId">execution session id</param>
    /// <param name="input">current input</param>
    /// <param name="kernelArguments">execution kernel arguments</param>
    /// <returns>KernelArguments, which includes a json array of strings as output. The flow result is also exposed through the context when completes.</returns>
    public async Task<FunctionResult> ExecuteFlowAsync(
        [Description("The flow to execute")] Flow flow,
        [Description("Execution session id")] string sessionId,
        [Description("Current input")] string input,
        [Description("Execution arguments")]
        KernelArguments? kernelArguments = null)
    {
        try
        {
            this._flowValidator.Validate(flow);
        }
        catch (Exception ex)
        {
            throw new KernelException("Invalid flow", ex);
        }

        var executor = new FlowExecutor(this._kernelBuilder, this._flowStatusProvider, this._globalPluginCollection, this._config);
        return await executor.ExecuteFlowAsync(flow, sessionId, input, kernelArguments ?? new KernelArguments()).ConfigureAwait(false);
    }
}
