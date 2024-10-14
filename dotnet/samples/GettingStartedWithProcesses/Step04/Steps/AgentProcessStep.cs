// Copyright (c) Microsoft. All rights reserved.
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;

namespace Step04.Steps;

/// <summary>
/// %%%
/// </summary>
public abstract class AgentProcessStep<TAgent> : KernelProcessStep where TAgent : KernelAgent
{
    /// <summary>
    /// %%%
    /// </summary>
    protected abstract string ServiceKey { get; }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="kernel"></param>
    /// <returns></returns>
    protected TAgent GetAgent(Kernel kernel) =>
        kernel.Services.GetRequiredKeyedService<TAgent>(this.ServiceKey);
}
