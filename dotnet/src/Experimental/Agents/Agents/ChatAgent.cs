// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

#pragma warning disable IDE0290 // Use primary constructor

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;
/// <summary>
/// A <see cref="LocalKernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class ChatAgent : LocalKernelAgent
{
    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <summary>
    /// Optional execution settings for the agent.
    /// </summary>
    public PromptExecutionSettings? ExecutionSettings { get; set; }

    /// <inheritdoc/>
    public override async IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        IEnumerable<ChatMessageContent> history,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        ChatHistory chat = [];

        if (!string.IsNullOrWhiteSpace(this.Instructions))
        {
            string instructions = (await this.FormatInstructionsAsync(cancellationToken).ConfigureAwait(false))!;

            chat.AddMessage(AuthorRole.System, instructions, name: this.Name);
        }

        chat.AddRange(history);

        var chatCompletionService = this.Kernel.GetRequiredService<IChatCompletionService>();

        var messages =
            await chatCompletionService.GetChatMessageContentsAsync(
                chat,
                this.ExecutionSettings,
                this.Kernel,
                cancellationToken).ConfigureAwait(false);

        foreach (var message in messages)
        {
            message.Source = new AgentMessageSource(this.Id).ToJson();

            yield return message;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="instructions">The agent instructions</param>
    /// <param name="description">The agent description (optional)</param>
    /// <param name="name">The agent name</param>
    /// <remarks>
    /// Enable <see cref="OpenAIPromptExecutionSettings.ToolCallBehavior"/> for agent plugins.
    /// </remarks>
    public ChatAgent(
        Kernel kernel,
        string? instructions,
        string? description,
        string? name)
       : base(kernel, instructions)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Description = description;
        this.Name = name;
    }
}
