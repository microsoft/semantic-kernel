// Copyright (c) Microsoft. All rights reserved.

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
    /// <param name="content">Content of the message</param>
    /// <param name="innerMessage">Inner content message reference</param>
    /// <param name="agent">Instance of The <see cref="KernelAgent"/> the message was created by.</param>
    public AgentMessage(AuthorRole role, string? content, object? innerMessage = null, KernelAgent? agent = null)
    {
        this.InnerMessage = innerMessage;
        this.Role = role;

        if (!string.IsNullOrEmpty(content))
        {
            this.Items.Add(new TextContent(content));
        }

        this.Agent = agent;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="AgentMessage"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="items">Instance of <see cref="ChatMessageContentItemCollection"/> with content items</param>
    /// <param name="innerMessage">Inner content message reference</param>
    /// <param name="agent">Instance of The <see cref="KernelAgent"/> the message was created by.</param>
    public AgentMessage(AuthorRole role, AgentMessageContentItemCollection items, object? innerMessage = null, KernelAgent? agent = null)
    {
        this.InnerMessage = innerMessage;
        this.Role = role;
        this._items = items;
        this.Agent = agent;
    }

    private AgentMessageContentItemCollection? _items;
}
