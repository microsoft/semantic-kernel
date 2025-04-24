// Copyright (c) Microsoft. All rights reserved.

using Magentic.Services;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Orchestration.Chat;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Magentic.Agents;

/// <summary>
/// %%% COMMENT
/// </summary>
public sealed class UserProxyAgent :
    PatternActor,
    IHandle<ChatMessages.Group>,
    IHandle<ChatMessages.Speak>,
    //IHandle<ChatMessages.Progress>, // %%% TODO: Progress
    IHandle<ChatMessages.Result>
{
    /// <summary>
    /// A common description for <see cref="UserProxyAgent"/>.
    /// </summary>
    public const string DefaultDescription = "The user. Provides input or clarification.";

    /// <summary>
    /// The well-known <see cref="AgentType"/> for <see cref="UserProxyAgent"/>.
    /// </summary>
    public const string TypeId = nameof(UserProxyAgent);

    private readonly IUXServices _uxService;
    private readonly TopicId _groupTopic;

    /// <summary>
    /// Initializes a new instance of the <see cref="UserProxyAgent"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="uxService">Services for UX interactions.</param>
    /// <param name="groupTopic">// %%% COMMENT</param>
    public UserProxyAgent(AgentId id, IAgentRuntime runtime, IUXServices uxService, TopicId groupTopic)
        : base(id, runtime, DefaultDescription)
    {
        this._uxService = uxService;
        this._groupTopic = groupTopic;
    }

    public async ValueTask HandleAsync(ChatMessages.Group item, MessageContext messageContext)
    {
        // User input already visible, only output assistant responses.
        if (item.Message.Role != AuthorRole.User)
        {
            await this._uxService.DisplayChatAsync(item.Message).ConfigureAwait(false);
        }
    }

    //public async ValueTask HandleAsync(ChatMessages.Progress item, MessageContext messageContext) // %%% TODO: Progress
    //{
    //    await this._uxService.DisplayProgressAsync(item).ConfigureAwait(false);
    //}

    public async ValueTask HandleAsync(ChatMessages.Result item, MessageContext messageContext)
    {
        await this._uxService.DisplayOutputAsync(item.Message).ConfigureAwait(false);
    }

    public async ValueTask HandleAsync(ChatMessages.Speak item, MessageContext messageContext)
    {
        string? userInput = null;

        do
        {
            userInput = await this._uxService.ReadInputAsync().ConfigureAwait(false);
        }
        while (string.IsNullOrWhiteSpace(userInput));

        await this.PublishMessageAsync(new ChatMessageContent(AuthorRole.User, userInput).ToGroup(), this._groupTopic).ConfigureAwait(false);
    }
}
