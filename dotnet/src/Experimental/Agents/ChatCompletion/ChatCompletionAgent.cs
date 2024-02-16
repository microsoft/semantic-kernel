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
    /// <param name="instructions">The instructions for the agent.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    public ChatCompletionAgent(string instructions, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null)
    {
        this._kernel = kernel;

        Verify.NotNullOrWhiteSpace(instructions, nameof(instructions));
        this._instructions = instructions;

        this._promptExecutionSettings = executionSettings;
    }

    /// <inheritdoc/>
    public override async Task<IReadOnlyList<AgentMessage>> InvokeAsync(IReadOnlyList<AgentMessage> messages, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        executionSettings = this.GetExecutionSettings(executionSettings);
        kernel = this.GetKernel(kernel);

        var chat = new ChatHistory(this._instructions);
        chat.AddRange(messages.Select(m => CreateChatMessage(m)));

        var chatMessageContent = await this.InvokeAsync(chat, executionSettings, kernel, cancellationToken).ConfigureAwait(false);

        return chatMessageContent.Select(m => this.CreateAgentMessage(m, kernel)).ToArray();
    }

    /// <summary>
    /// Invokes the agent to process the given messages and generate a response.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(ChatHistory messages, PromptExecutionSettings? executionSettings = null, Kernel? kernel = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        executionSettings = this.GetExecutionSettings(executionSettings);
        kernel = this.GetKernel(kernel);

        // TODO: Use kernel.ServiceSelector after it has been refactored to not require function and kernel arguments.
        var chatCompletionService = kernel.GetRequiredService<IChatCompletionService>();

        return await chatCompletionService.GetChatMessageContentsAsync(
            messages,
            executionSettings,
            kernel,
            cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Returns the kernel instance to be used, either from the provided override or the class instance one.
    /// </summary>
    /// <param name="kernelOverride">Optional kernel instance to be used instead of the class instance one.</param>
    /// <returns>The kernel instance to be used.</returns>
    private Kernel GetKernel(Kernel? kernelOverride)
    {
        return kernelOverride ?? this._kernel ?? throw new KernelException("Kernel is not provided.");
    }

    /// <summary>
    /// Returns the prompt execution settings to be used, either from the provided override or the class instance one.
    /// </summary>
    /// <param name="settingsOverride">Optional prompt execution settings to be used instead of the class instance ones.</param>
    /// <returns>The prompt execution settings to be used, or null if no settings are provided or available.</returns>
    private PromptExecutionSettings? GetExecutionSettings(PromptExecutionSettings? settingsOverride)
    {
        return this._promptExecutionSettings ?? settingsOverride;
    }

    /// <summary>
    /// Creates a chat message from an agent message.
    /// </summary>
    /// <param name="message">The agent message to be converted.</param>
    /// <returns>A chat message created from the agent message.</returns>
    private static ChatMessageContent CreateChatMessage(AgentMessage message)
    {
        Verify.NotNull(message, nameof(message));

        if (message.Role == AuthorRole.Assistant)
        {
            if (message.Items.Count == 0)
            {
                if (message.InnerMessage is null)
                {
                    throw new KernelException("Agent message must have at least one piece of content for the assistant role.");
                }

                // The inner message is one of the derivatives of the chat message content, but we don't have enough information about it.
                // Therefore, we do our best to handle it by returning it as is.
                if (message.InnerMessage.GetType().IsSubclassOf(typeof(ChatMessageContent)))
                {
                    return (ChatMessageContent)message.InnerMessage;
                }
            }
        }

        if (message.Role == AuthorRole.Tool || message.Role == AuthorRole.Assistant)
        {
            if (message.Items.Count != 1)
            {
                throw new KernelException($"Agent message should only have one piece of content for the '{message.Role}' role.");
            }

            if (message.Items[0] is not TextContent textContent)
            {
                throw new KernelException($"Agent message has an unsupported content type '{message.Items[0].GetType()}' for the '{message.Role}' role.");
            }

            return new ChatMessageContent(
                role: message.Role,
                content: textContent.Text,
                encoding: textContent.Encoding,
                innerContent: message,
                metadata: message.Metadata);
        }

        // All other roles
        return new ChatMessageContent(
            role: message.Role,
            items: new(message.Items),
            innerContent: message,
            metadata: message.Metadata);
    }

    /// <summary>
    /// Creates an agent message from a chat message.
    /// </summary>
    /// <param name="message">The chat message to be converted.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <returns>An agent message created from the chat message.</returns>
    private AgentMessage CreateAgentMessage(ChatMessageContent message, Kernel kernel)
    {
        Verify.NotNull(message, nameof(message));

        return new AgentMessage(
            role: message.Role,
            content: message.Content,
            innerMessage: message,
            agent: this,
            kernel: kernel,
            metadata: message.Metadata);
    }

    private readonly Kernel? _kernel;
    private readonly string _instructions;
    private readonly PromptExecutionSettings? _promptExecutionSettings;
}
