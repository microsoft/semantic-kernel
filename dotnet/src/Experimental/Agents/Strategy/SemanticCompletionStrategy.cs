// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// Completion strategy based on the semantic evaluation of the chat.
/// </summary>
public sealed class SemanticCompletionStrategy : CompletionStrategy
{
    private readonly string _instructions;
    private readonly IChatCompletionService _service;
    private readonly PromptExecutionSettings? _executionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="SemanticCompletionStrategy"/> class.
    /// </summary>
    /// <param name="service">A chat-completion service.</param>
    /// <param name="instructions">The evaluation instructions.</param>
    /// <param name="executionSettings">The execution settings for the strategy.</param>
    public SemanticCompletionStrategy(IChatCompletionService service, string instructions, PromptExecutionSettings? executionSettings = null)
    {
        this._service = service;
        this._instructions = instructions;
        this._executionSettings = executionSettings;
    }

    /// <inheritdoc/>
    public override async Task<bool> IsCompleteAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        var chat = new ChatHistory(this._instructions);

        chat.AddRange(history);

        var messages =
            await this._service.GetChatMessageContentsAsync(
                chat,
                this._executionSettings,
                kernel: null,
                cancellationToken).ConfigureAwait(false);

        var result = messages[0].Content;

        return result?.Contains(bool.TrueString) ?? false; // $$$ TODO: STRONGER
    }
}
