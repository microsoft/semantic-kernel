// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represent an agent that is built around the SK ChatCompletion API and leverages the API's capabilities.
/// </summary>
public sealed class ChatCompletionAgent : KernelAgent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="instructions">The instructions for the agent.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    public ChatCompletionAgent(Kernel kernel, string instructions, PromptExecutionSettings? executionSettings = null) : base(kernel)
    {
        Verify.NotNullOrWhiteSpace(instructions, nameof(instructions));
        this._instructions = instructions;

        this._promptExecutionSettings = executionSettings;
    }

    /// <inheritdoc/>
    public override async Task<IReadOnlyList<AgentMessage>> InvokeAsync(IReadOnlyList<AgentMessage> messages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chat = new ChatHistory(this._instructions);
        chat.AddRange(messages.Select(m => CreateChatMessage(m)));

        var chatMessageContent = await this.InvokeAsync(chat, cancellationToken).ConfigureAwait(false);

        return chatMessageContent.Select(m => this.CreateAgentMessage(m)).ToArray();
    }

    /// <summary>
    /// Invokes the agent to process the given messages and generate a response.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(ChatHistory messages, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        return await chatCompletionService.GetChatMessageContentsAsync(
            messages,
            this._promptExecutionSettings,
            this.Kernel,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Creates a chat message from an agent message.
    /// </summary>
    /// <param name="message">The agent message to be converted.</param>
    /// <returns>A chat message created from the agent message.</returns>
    private static ChatMessageContent CreateChatMessage(AgentMessage message)
    {
        Verify.NotNull(message, nameof(message));

        if (message.Items is not { Count: > 0 })
        {
            throw new KernelException("Agent message has no content.");
        }

        if (message.Role == AuthorRole.User)
        {
            return new ChatMessageContent(role: message.Role, items: new(message.Items), innerContent: message);
        }

        if (message.Role == AuthorRole.Assistant)
        {
            if (message.Items.Count != 1)
            {
                throw new KernelException("Agent message can't have more than one piece of content for the assistant role.");
            }

            var content = message.Items.Single();

            if (content is TextContent textContent)
            {
                return new ChatMessageContent(
                    role: message.Role,
                    content: textContent.Text,
                    encoding: textContent.Encoding,
                    metadata: textContent.Metadata,
                    innerContent: message);
            }

            throw new KernelException($"Agent message has an unsupported content type '{content.GetType()}' for the assistant role.");
        }

        return new ChatMessageContent(role: message.Role, items: new(message.Items), innerContent: message);
    }

    /// <summary>
    /// Creates an agent message from a chat message.
    /// </summary>
    /// <param name="message">The chat message to be converted.</param>
    /// <returns>An agent message created from the chat message.</returns>
    private AgentMessage CreateAgentMessage(ChatMessageContent message)
    {
        Verify.NotNull(message, nameof(message));

        return new AgentMessage(
            role: message.Role,
            content: message.Content,
            innerMessage: message,
            agent: this);
    }

    private readonly string _instructions;
    private readonly PromptExecutionSettings? _promptExecutionSettings;
}
