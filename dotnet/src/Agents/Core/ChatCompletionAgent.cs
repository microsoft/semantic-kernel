// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.Extensions;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class ChatCompletionAgent : ChatHistoryKernelAgent
{
    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <summary>
    /// Additional instructions to always append to end of history (optional)
    /// </summary>
    public string? ExtraInstructions { get; set; }

    /// <summary>
    /// Optional execution settings for the agent.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; set; }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        IReadOnlyList<ChatMessageContent> history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        ChatHistory chat = new();
        await AddFormattedInstructionsToHistoryAsync(this.Instructions, cancellationToken).ConfigureAwait(false);
        chat.AddRange(history);
        await AddFormattedInstructionsToHistoryAsync(this.ExtraInstructions, cancellationToken).ConfigureAwait(false);

        var messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                this.ExecutionSettings,
                this.Kernel,
                cancellationToken).ConfigureAwait(false);

        foreach (var message in messages ?? Array.Empty<ChatMessageContent>())
        {
            // TODO: MESSAGE SOURCE - ISSUE #5731
            message.AuthorName = this.Name;

            yield return message;
        }

        async Task AddFormattedInstructionsToHistoryAsync(string? instructions, CancellationToken cancellationToken)
        {
            if (!string.IsNullOrWhiteSpace(instructions))
            {
                instructions = (await this.FormatInstructionsAsync(instructions, cancellationToken).ConfigureAwait(false))!;

                chat.Add(new ChatMessageContent(AuthorRole.System, instructions) { AuthorName = this.Name });
            }
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatCompletionAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="instructions">The agent instructions</param>
    /// <param name="description">The agent description (optional)</param>
    /// <param name="name">The agent name</param>
    /// <remarks>
    /// NOTE: Enable OpenAIPromptExecutionSettings.ToolCallBehavior for agent plugins.
    /// (<see cref="ChatCompletionAgent.ExecutionSettings"/>)
    /// </remarks>
    public ChatCompletionAgent(
        Kernel kernel,
        string? instructions = null,
        string? description = null,
        string? name = null)
       : base(kernel, instructions)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Description = description;
        this.Name = name;
    }
}
