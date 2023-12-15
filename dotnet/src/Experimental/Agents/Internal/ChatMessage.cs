// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.SemanticKernel.Experimental.Agents.Models;

namespace Microsoft.SemanticKernel.Experimental.Agents.Internal;

/// <summary>
/// Represents a message that is part of an agent thread.
/// </summary>
internal sealed class ChatMessage : IChatMessage
{
    /// <inheritdoc/>
    public string Id { get; }

    /// <inheritdoc/>
    public string? AgentId { get; }

    /// <inheritdoc/>
    public string Content { get; }

    /// <inheritdoc/>
    public string Role { get; }

    /// <inheritdoc/>
    public ReadOnlyDictionary<string, object> Properties { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessage"/> class.
    /// </summary>
    internal ChatMessage(ThreadMessageModel model)
    {
        var content = (IEnumerable<ThreadMessageModel.ContentModel>)model.Content;
        var text = content.First().Text?.Value ?? string.Empty;

        this.Id = model.Id;
        this.AgentId = string.IsNullOrWhiteSpace(model.AgentId) ? null : model.AgentId;
        this.Role = model.Role;
        this.Content = text;
        this.Properties = new ReadOnlyDictionary<string, object>(model.Metadata);
    }
}
