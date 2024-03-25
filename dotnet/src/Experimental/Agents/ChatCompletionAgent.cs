// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represent an agent that is built around the SK ChatCompletion API and leverages the API's capabilities.
/// </summary>
public sealed class ChatCompletionAgent
{
    private readonly Kernel _kernel;
    private readonly string _instructions;
    private readonly PromptExecutionSettings? _promptExecutionSettings;

    /// <summary>
    /// Gets the name of the agent.
    /// </summary>
    public string Name { get; }

    /// <summary>
    /// Gets the description of the agent.
    /// </summary>
    public string Description { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="name">The name of the agent.</param>
    /// <param name="instructions">The instructions for the agent.</param>
    /// <param name="description">The optional description of the agent.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    public ChatCompletionAgent(Kernel kernel, string name, string instructions, string description = null, PromptExecutionSettings? executionSettings = null)
    {
        Verify.NotNull(kernel, nameof(kernel));
        this._kernel = kernel;

        Verify.NotNullOrWhiteSpace(name, nameof(name));
        this.Name = name;

        Verify.NotNullOrWhiteSpace(instructions, nameof(instructions));
        this._instructions = instructions;

        this.Description = description ?? string.Empty;

        this._promptExecutionSettings = executionSettings;
    }

    /// <summary>
    /// Invokes the agent to process the given messages and generate a response.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    public async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(IReadOnlyList<ChatMessageContent> messages, CancellationToken cancellationToken = default)
    {
        var chat = new ChatHistory();
        chat.AddRange(messages);
        chat.AddSystemMessage(this._instructions);

        var chatCompletionService = this.GetChatCompletionService();

        var chatMessageContent = await chatCompletionService.GetChatMessageContentsAsync(
            chat,
            this._promptExecutionSettings,
            this._kernel,
            cancellationToken).ConfigureAwait(false);

        return chatMessageContent;
    }

    /// <summary>
    /// Resolves and returns the chat completion service.
    /// </summary>
    /// <returns>An instance of the chat completion service.</returns>
    private IChatCompletionService GetChatCompletionService()
    {
        return this._kernel.GetRequiredService<IChatCompletionService>();
    }
}
