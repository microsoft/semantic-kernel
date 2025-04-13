//// Copyright (c) Microsoft. All rights reserved.

//using System.Collections.Generic;
//using System.Linq;
//using System.Threading.Tasks;
//using Microsoft.AgentRuntime;

//namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

///// <summary>
///// %%% COMMENT
///// </summary>
//internal sealed class GroupChatActor : AgentActor
//{
//    private readonly List<ChatMessageContent> _cache;
//    private readonly TopicId _chatTopic;
//    private AgentThread? _thread;

//    /// <summary>
//    /// Initializes a new instance of the <see cref="GroupChatActor"/> class.
//    /// </summary>
//    /// <param name="id">The unique identifier of the agent.</param>
//    /// <param name="runtime">The runtime associated with the agent.</param>
//    /// <param name="agent">An <see cref="Agent"/>.</param>
//    /// <param name="chatTopic">The unique topic used to broadcast to the entire chat.</param>
//    public GroupChatActor(AgentId id, IAgentRuntime runtime, Agent agent, TopicId chatTopic)
//        : base(id, runtime, agent)
//    {
//        this._cache = [];
//        this._chatTopic = chatTopic;

//        this.RegisterHandler<ChatMessages.Group>(this.OnGroupMessageAsync);
//        this.RegisterHandler<ChatMessages.Reset>(this.OnResetMessageAsync);
//        this.RegisterHandler<ChatMessages.Speak>(this.OnSpeakMessageAsync);
//    }

//    private ValueTask OnGroupMessageAsync(ChatMessages.Group message, MessageContext context)
//    {
//        this._cache.Add(message.Message);

//        return ValueTask.CompletedTask;
//    }

//    private async ValueTask OnResetMessageAsync(ChatMessages.Reset message, MessageContext context)
//    {
//        if (this._thread is not null)
//        {
//            await this._thread.DeleteAsync().ConfigureAwait(false);
//            this._thread = null;
//        }
//    }

//    private async ValueTask OnSpeakMessageAsync(ChatMessages.Speak message, MessageContext context)
//    {
//        AgentResponseItem<ChatMessageContent>[] responses = await this.Agent.InvokeAsync(this._cache, this._thread).ToArrayAsync().ConfigureAwait(false);
//        AgentResponseItem<ChatMessageContent> response = responses.First();
//        this._thread ??= response.Thread;
//        this._cache.Clear();
//        ChatMessageContent output =
//            new(response.Message.Role, string.Join("\n\n", responses.Select(response => response.Message)))
//            {
//                AuthorName = response.Message.AuthorName,
//            };
//        await this.PublishMessageAsync(output.ToGroup(), this._chatTopic).ConfigureAwait(false);
//    }
//}
