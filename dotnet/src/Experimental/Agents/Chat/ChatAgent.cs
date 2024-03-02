// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Microsoft.SemanticKernel.Experimental.Agents.Chat;

/// <summary>
/// A <see cref="KernelAgent"/> specialization based on <see cref="IChatCompletionService"/>.
/// </summary>
public sealed class ChatAgent : KernelAgent<ChatChannel>
{
    private readonly PromptExecutionSettings? _executionSettings;

    /// <inheritdoc/>
    public override string? Description { get; }

    /// <inheritdoc/>
    public override string Id { get; }

    /// <inheritdoc/>
    public override string? Instructions { get; }

    /// <inheritdoc/>
    public override string? Name { get; }

    /// <inheritdoc/>
    protected internal override Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new ChatChannel(nexus.History, this._executionSettings));
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatAgent"/> class.
    /// </summary>
    /// <param name="kernel"></param>
    /// <param name="instructions"></param>
    /// <param name="description"></param>
    /// <param name="name"></param>
    /// <param name="executionSettings"></param>
    public ChatAgent(
        Kernel kernel,
        string? instructions,
        string? description,
        string? name,
        PromptExecutionSettings? executionSettings = null)
       : base(kernel)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Description = description;
        this.Instructions = instructions;
        this.Name = name;
        this._executionSettings = executionSettings ?? new OpenAIPromptExecutionSettings { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions }; // $$$

        if (this._executionSettings is OpenAIPromptExecutionSettings openaiSettings)
        {
            openaiSettings.ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions; // $$$
        }
    }
}
