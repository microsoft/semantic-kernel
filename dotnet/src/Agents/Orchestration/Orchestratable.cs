// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%% COMMENT
/// </summary>
public abstract class Orchestratable
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="externalTopic"></param>
    /// <param name="targetActor"></param>
    /// <returns></returns>
    protected internal abstract ValueTask<AgentType> RegisterAsync(TopicId externalTopic, AgentType? targetActor);
}
