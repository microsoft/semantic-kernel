﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors.Runtime;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Runtime;

namespace Microsoft.SemanticKernel;

internal sealed class AgentStepActor : StepActor, IAgentStep
{
    private readonly ILogger? _logger;

    private readonly AgentFactory _agentFactory;

    internal KernelProcessAgentStep? _daprAgentStepInfo;

    /// <summary>
    /// Initializes a new instance of the <see cref="ProxyActor"/> class.
    /// </summary>
    /// <param name="host">The Dapr host actor</param>
    /// <param name="kernel">An instance of <see cref="Kernel"/></param>
    /// <param name="registeredProcesses">The registered processes</param>
    /// <param name="agentFactory">An instance of <see cref="AgentFactory"/></param>
    public AgentStepActor(ActorHost host, Kernel kernel, IReadOnlyDictionary<string, KernelProcess> registeredProcesses, AgentFactory agentFactory)
        : base(host, kernel, registeredProcesses)
    {
        this._agentFactory = agentFactory;
        this._logger = this._kernel.LoggerFactory?.CreateLogger(typeof(KernelProxyStep)) ?? new NullLogger<ProxyActor>();
    }

    internal override KernelProcessStep GetStepInstance()
    {
        return (KernelProcessAgentExecutor)ActivatorUtilities.CreateInstance(this._kernel.Services, this._innerStepType!, this._agentFactory, this._daprAgentStepInfo!);
    }

    internal override Dictionary<string, Dictionary<string, object?>?> GenerateInitialInputs()
    {
        return this.FindInputChannels(this._functions, null, this._logger, agentDefinition: this._daprAgentStepInfo!.AgentDefinition);
    }

    public async Task InitializeAgentStepAsync(string processId, string stepId, string? parentProcessId)
    {
        Verify.NotNullOrWhiteSpace(processId, nameof(processId));
        Verify.NotNullOrWhiteSpace(stepId, nameof(stepId));

        this._daprAgentStepInfo = this._registeredProcesses.GetStepInfo<KernelProcessAgentStep>(processId, stepId);
        await base.InitializeStepAsync(processId, stepId, parentProcessId).ConfigureAwait(false);
    }
}
