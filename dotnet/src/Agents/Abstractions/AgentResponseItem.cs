// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Container class that holds a <see cref="ChatMessageContent"/> or <see cref="StreamingChatMessageContent"/> and an <see cref="AgentThread"/>.
/// </summary>
public class AgentResponseItem<TMessage>
{
    private readonly TMessage _message;
    private readonly AgentThread _thread;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentResponseItem{T}"/> class.
    /// </summary>
    /// <param name="message">The chat message content.</param>
    /// <param name="thread">The conversation thread associated with the response.</param>
    public AgentResponseItem(TMessage message, AgentThread thread)
    {
        Verify.NotNull(message);
        Verify.NotNull(thread);

        this._message = message;
        this._thread = thread;
    }

    /// <summary>
    /// Gets the chat message content.
    /// </summary>
    public TMessage Message => this._message;

    /// <summary>
    /// Gets the conversation thread associated with the response.
    /// </summary>
    public AgentThread Thread => this._thread;
}
