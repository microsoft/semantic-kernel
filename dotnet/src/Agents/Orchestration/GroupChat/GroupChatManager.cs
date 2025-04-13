//// Copyright (c) Microsoft. All rights reserved.

//using System;
//using System.Linq;
//using System.Threading.Tasks;
//using Microsoft.AgentRuntime;

//namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

///// <summary>
///// A <see cref="RuntimeAgent"/> that orchestrates a team of agents.
///// </summary>
//internal sealed class GroupChatManager : ChatManager
//{
//    private readonly TaskCompletionSource<ChatMessageContent> _completionSource;

//    /// <summary>
//    /// Initializes a new instance of the <see cref="GroupChatManager"/> class.
//    /// </summary>
//    /// <param name="id">The unique identifier of the agent.</param>
//    /// <param name="runtime">The runtime associated with the agent.</param>
//    /// <param name="team">The team of agents being orchestrated</param>
//    /// <param name="completionSource">Signals completion.</param>
//    public GroupChatManager(AgentId id, IAgentRuntime runtime, ChatTeam team, TaskCompletionSource<ChatMessageContent> completionSource)
//        : base(id, runtime, team, completionSource)
//    {
//        this._completionSource = completionSource;
//    }

//    /// <inheritdoc/>
//    protected override Task<TopicId?> PrepareTaskAsync()
//    {
//        return this.SelectAgentAsync();
//    }

//    /// <inheritdoc/>
//    protected override Task<TopicId?> SelectAgentAsync()
//    {
//        // %%% PLACEHOLDER
//#pragma warning disable CA5394 // Do not use insecure randomness
//        int index = Random.Shared.Next(this.Team.Count + 1);
//#pragma warning restore CA5394 // Do not use insecure randomness
//        var topics = this.Team.Values.Select(value => value.Topic).ToArray();
//        TopicId? topic = null;
//        if (index < this.Team.Count)
//        {
//            topic = topics[index];
//        }
//        return System.Threading.Tasks.Task.FromResult(topic);
//    }
//}
