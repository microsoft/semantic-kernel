// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents;

[Experimental("SKEXP0110")]
internal sealed class SemanticKernelAIAgentSession : MAAI.AgentSession
{
    private readonly Func<AgentThread, JsonSerializerOptions?, JsonElement> _threadSerializer;

    internal SemanticKernelAIAgentSession(AgentThread thread, Func<AgentThread, JsonSerializerOptions?, JsonElement> threadSerializer)
    {
        Throw.IfNull(thread);
        Throw.IfNull(threadSerializer);

        this.InnerThread = thread;
        this._threadSerializer = threadSerializer;
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
