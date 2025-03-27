// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// A <see cref="ManagedAgent"/> that responds to a <see cref="ManagerAgent"/>.
/// </summary>
public abstract class ManagedAgent : RuntimeAgent
{
    /// <summary>
    /// The common topic for group-chat.
    /// </summary>
    public static readonly TopicId GroupChatTopic = new(nameof(GroupChatTopic));

    /// <summary>
    /// The common topic for hidden-chat.
    /// </summary>
    public static readonly TopicId InnerChatTopic = new(nameof(InnerChatTopic));

    /// <summary>
    /// Initializes a new instance of the <see cref="ManagedAgent"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="description">The agent description.</param>
    protected ManagedAgent(AgentId id, IAgentRuntime runtime, string description)
        : base(id, runtime, description)
    {
        this.RegisterHandler<Messages.Group>(this.OnGroupMessageAsync);
        this.RegisterHandler<Messages.Reset>(this.OnResetMessageAsync);
        this.RegisterHandler<Messages.Speak>(this.OnSpeakMessageAsync);
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <returns></returns>
    protected abstract ValueTask ResetAsync();

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    protected abstract ValueTask RecieveMessageAsync(ChatMessageContent message);

    /// <summary>
    /// %%%
    /// </summary>
    /// <returns></returns>
    protected abstract ValueTask<ChatMessageContent> SpeakAsync();

    private ValueTask OnGroupMessageAsync(Messages.Group message, MessageContext context)
    {
        return this.RecieveMessageAsync(message.Message);
    }

    private ValueTask OnResetMessageAsync(Messages.Reset message, MessageContext context)
    {
        return this.ResetAsync();
    }

    private async ValueTask OnSpeakMessageAsync(Messages.Speak message, MessageContext context)
    {
        ChatMessageContent response = await this.SpeakAsync().ConfigureAwait(false);
        await this.PublishMessageAsync(response.ToGroup(), GroupChatTopic).ConfigureAwait(false);
    }
}
