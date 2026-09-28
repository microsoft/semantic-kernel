// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents;

[Experimental("SKEXP0110")]
internal sealed class SemanticKernelAIAgentSession : MAAI.AgentSession
{
    internal SemanticKernelAIAgentSession(AgentThread thread)
    {
        Throw.IfNull(thread);
        this.InnerThread = thread;
    }

    /// <summary>
    /// Gets the underlying Semantic Kernel Agent Framework <see cref="AgentThread"/>.
    /// </summary>
    public AgentThread InnerThread { get; }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Throw.IfNull(serviceType);

        return serviceKey is null && serviceType.IsInstanceOfType(this.InnerThread)
        ? this.InnerThread
        : base.GetService(serviceType, serviceKey);
    }
}
