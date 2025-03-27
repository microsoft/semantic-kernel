// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration.HandOff;

internal class HandoffOrchestration : AgentOrchestration
{
    private const string TopicType = nameof(HandoffOrchestration); // %%% NAME
    private readonly Agent[] _agents;
    private readonly ReadOnlyDictionary<Agent, TopicId> _topics;

    public HandoffOrchestration(IAgentRuntime runtime, params Agent[] agents)
        : base(runtime)
    {
        //Verify.NotEmpty(agents, nameof(agents)); // %%% TODO
        this._agents = agents;
        this._topics =
            agents
                .ToDictionary(
                    agent => agent,
                    agent => new TopicId(TopicType, $"{agent.GetType().Name}{Guid.NewGuid()}"))
                .AsReadOnly();
    }

    protected override async ValueTask MessageTaskAsync(ChatMessageContent message)
    {
        await Task.Delay(0).ConfigureAwait(false);
        //await this.Runtime.PublishMessageAsync(message, this._topics[this._agents[0]]).ConfigureAwait(false);
    }

    protected override async ValueTask RegisterAsync()
    {
        //foreach (Agent agent in this._agents)
        //{
        //    await this.Runtime.RegisterAgentAsync(agent, this._topics[agent]).ConfigureAwait(false);
        //}
    }
}
