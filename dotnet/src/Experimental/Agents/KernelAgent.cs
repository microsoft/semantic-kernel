// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represent a base class for agents.
/// </summary>
public abstract class KernelAgent
{
    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; internal set; }

    /// <summary>
    /// The name of the agent
    /// </summary>
    public string Name { get; internal set; }

    /// <summary>
    /// The description of the agent
    /// </summary>
    public string? Description { get; internal set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="name">The agent name.</param>
    /// <param name="description">The agent description.</param>
    protected KernelAgent(Kernel kernel, string name, string? description)
    {
        Verify.NotNull(kernel, nameof(kernel));
        this.Kernel = kernel;
        this.Name = name;
        this.Description = description;
    }

    /// <summary>
    /// Invokes the agent to process the given messages and generate a response.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    public abstract Task<IReadOnlyList<ChatMessageContent>> InvokeAsync(IReadOnlyList<ChatMessageContent> messages, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default);

    /// <summary>
    /// Invokes the agent to process the given messages and generate a response as a stream.
    /// </summary>
    /// <param name="messages">A list of the messages for the agent to process.</param>
    /// <param name="executionSettings">The AI execution settings (optional).</param>
    /// <param name="cancellationToken">An optional <see cref="CancellationToken"/> to cancel the operation.</param>
    /// <returns>List of messages representing the agent's response.</returns>
    /// <returns>Streaming list of content updates representing the agent's response.</returns>
    public abstract IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(IReadOnlyList<ChatMessageContent> messages, PromptExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default);
}
