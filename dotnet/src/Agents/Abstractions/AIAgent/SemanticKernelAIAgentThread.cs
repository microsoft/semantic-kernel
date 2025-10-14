// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents;

[Experimental("SKEXP0110")]
internal sealed class SemanticKernelAIAgentThread : MAAI.AgentThread
{
    private readonly Func<AgentThread, JsonSerializerOptions?, JsonElement> _threadSerializer;

    internal SemanticKernelAIAgentThread(AgentThread thread, Func<AgentThread, JsonSerializerOptions?, JsonElement> threadSerializer)
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
    public override JsonElement Serialize(JsonSerializerOptions? jsonSerializerOptions = null)
        => this._threadSerializer(this.InnerThread, jsonSerializerOptions);

    public override object? GetService(Type serviceType, object? serviceKey = null)
        => base.GetService(serviceType, serviceKey)
        ?? (serviceType == typeof(AgentThread) && serviceKey is null
        ? this.InnerThread
        : null);
}
