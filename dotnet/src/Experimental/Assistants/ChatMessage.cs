// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Assistants.Models;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents a message that is part of an assistant thread.
/// </summary>
public class ChatMessage
{
    /// <summary>
    /// The message identifier (which can be referenced in API endpoints).
    /// </summary>
    public string Id { get; }

    /// <summary>
    /// The id of the assistant associated with the a message where role = "assistant", otherwise null.
    /// </summary>
    public string? AssistantId { get; }

    /// <summary>
    /// The chat message content.
    /// </summary>
    public string Content { get; }

    /// <summary>
    /// The role associated with the chat message.
    /// </summary>
    public string Role { get; }

    /// <summary>
    /// Properties associated with the message.
    /// </summary>
    public ReadOnlyDictionary<string, object> Properties { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessage"/> class.
    /// </summary>
    internal ChatMessage(ThreadMessageModel model)
    {
        var content = (IEnumerable<ThreadMessageModel.ContentModel>)model.Content;
        var text = content.First().Text?.Value ?? string.Empty;

        this.Id = model.Id;
        this.AssistantId = string.IsNullOrWhiteSpace(model.AssistantId) ? null : model.AssistantId;
        this.Role = model.Role;
        this.Content = text;
        this.Properties = new ReadOnlyDictionary<string, object>(model.Metadata);
    }
}
