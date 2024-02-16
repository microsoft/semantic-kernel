// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents agent message used by agents inherited from <see cref="KernelAgent" /> class.
/// </summary>
public class AgentMessage
{
    /// <summary>
    /// The inner message representation. Use this to bypass the current abstraction.
    /// </summary>
    public object? InnerMessage { get; set; }

    /// <summary>
    /// Role of the author of the message.
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// The <see cref="KernelAgent"/> the message was created by.
    /// </summary>
    public KernelAgent? Agent { get; set; }

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel? Kernel { get; set; }

    /// <summary>
    /// The metadata associated with the content.
    /// </summary>
    public IReadOnlyDictionary<string, object?>? Metadata { get; }

    /// <summary>
    /// Agent message content items.
    /// </summary>
    public AgentMessageContentItemCollection Items =>
        this._items ??
        Interlocked.CompareExchange(ref this._items, new AgentMessageContentItemCollection(), null) ??
        this._items;

    /// <summary>
    /// Creates a new instance of the <see cref="AgentMessage"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">The content of the message can be empty if the message represents a tool/function call,
    /// the details of which can be obtained from the <see cref="AgentMessage.InnerMessage"/> property of the class.</param>
    /// <param name="innerMessage">Inner content message reference</param>
    /// <param name="agent">Instance of The <see cref="KernelAgent"/> the message was created by.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="metadata">The metadata associated with the message.</param>
    public AgentMessage(AuthorRole role, string? content, object? innerMessage = null, KernelAgent? agent = null, Kernel? kernel = null, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        this.Role = role;

        if (!string.IsNullOrEmpty(content))
        {
            this.Items.Add(new TextContent(content));
        }

        this.InnerMessage = innerMessage;
        this.Agent = agent;
        this.Kernel = kernel;
        this.Metadata = metadata;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="AgentMessage"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="items">Instance of <see cref="ChatMessageContentItemCollection"/> with content items</param>
    /// <param name="innerMessage">Inner content message reference</param>
    /// <param name="agent">Instance of The <see cref="KernelAgent"/> the message was created by.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="metadata">The metadata associated with the message.</param>
    public AgentMessage(AuthorRole role, AgentMessageContentItemCollection items, object? innerMessage = null, KernelAgent? agent = null, Kernel? kernel = null, IReadOnlyDictionary<string, object?>? metadata = null)
    {
        this.Role = role;
        this._items = items;
        this.InnerMessage = innerMessage;
        this.Agent = agent;
        this.Kernel = kernel;
        this.Metadata = metadata;
    }

    private AgentMessageContentItemCollection? _items;
}
