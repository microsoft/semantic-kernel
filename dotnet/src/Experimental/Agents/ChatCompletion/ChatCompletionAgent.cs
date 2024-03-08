// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
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
    /// <param name="name">The agent name.</param>
    /// <param name="description">The agent description.</param>
    /// <param name="executionSettings">The optional execution settings for the agent. If not provided, default settings will be used.</param>
    public ChatCompletionAgent(Kernel kernel, string instructions, string name, string? description, PromptExecutionSettings? executionSettings = null) : base(kernel, name, description)
    {
        Verify.NotNullOrWhiteSpace(instructions, nameof(instructions));
        this._kernel = kernel;

        Verify.NotNull(instructions, nameof(instructions));
        this._instructions = instructions;

        this._promptExecutionSettings = executionSettings;
    }

    /// <inheritdoc/>
    public override async Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(IReadOnlyList<ChatMessageContent> messages, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chat = new ChatHistory(this._instructions);
        chat.AddRange(messages);

        // TODO: Use kernel.ServiceSelector after it has been refactored to not require function and kernel arguments.
        var chatCompletionService = this._kernel.GetRequiredService<IChatCompletionService>();

        var chatMessageContent = await chatCompletionService.GetChatMessageContentsAsync(
            chat,
            executionSettings ?? this._promptExecutionSettings,
            this._kernel,
            cancellationToken).ConfigureAwait(false);

        return chatMessageContent.Select(m => { m.Source = this; return m; }).ToArray();
    }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(IReadOnlyList<ChatMessageContent> messages, PromptExecutionSettings? executionSettings = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(messages);

        var chat = new ChatHistory(this._instructions);
        chat.AddRange(messages);

        // TODO: Use kernel.ServiceSelector after it has been refactored to not require function and kernel arguments.
        var chatCompletionService = this._kernel.GetRequiredService<IChatCompletionService>();

        var chatMessageContent = chatCompletionService.GetStreamingChatMessageContentsAsync(
            chat,
            executionSettings ?? this._promptExecutionSettings,
            this._kernel,
            cancellationToken).ConfigureAwait(false);

        await foreach (var chatMessage in chatMessageContent)
        {
            chatMessage.Source = this;

            yield return chatMessage;
        }
    }

    private readonly Kernel _kernel;
    private readonly string _instructions;
    private readonly PromptExecutionSettings? _promptExecutionSettings;
}
