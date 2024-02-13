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
public abstract class ChatCompletionAgent : KernelAgent
{
    private readonly string _instructions;
    private readonly PromptExecutionSettings? _promptExecutionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="instructions">The instructions for the agent.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    protected ChatCompletionAgent(Kernel kernel, string instructions, PromptExecutionSettings? executionSettings = null) : base(kernel)
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
        chat.AddRange(messages.Select(m => this.CreateChatMessage(m)));

        var chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        var chatMessageContent = await chatCompletionService.GetChatMessageContentsAsync(
            chat,
            this._promptExecutionSettings,
            this.Kernel,
            cancellationToken).ConfigureAwait(false);

        return chatMessageContent.Select(m => this.CreateAgentMessage(m)).ToArray();
    }

    /// <summary>
    /// Creates a chat message from an agent message.
    /// </summary>
    /// <param name="message">The agent message to be converted.</param>
    /// <returns>A chat message created from the agent message.</returns>
    protected abstract ChatMessageContent CreateChatMessage(AgentMessage message);

    /// <summary>
    /// Creates an agent message from a chat message.
    /// </summary>
    /// <param name="message">The chat message to be converted.</param>
    /// <returns>An agent message created from the chat message.</returns>
    protected abstract AgentMessage CreateAgentMessage(ChatMessageContent message);
}
