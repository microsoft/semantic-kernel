// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.SemanticKernel.Experimental.Agents.Models;
using static Microsoft.SemanticKernel.Experimental.Agents.IChatMessage;

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

    public IList<IAnnotation> Annotations { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessage"/> class.
    /// </summary>
    internal ChatMessage(ThreadMessageModel model)
    {
        var content = model.Content.First();
        var text = content.Text?.Value ?? string.Empty;
        this.Annotations = content.Text!.Annotations.Select(a => new Annotation(a.Text, a.StartIndex, a.EndIndex, a.FileCitation?.FileId ?? a.FilePath!.FileId, a.FileCitation?.Quote)).ToArray();

        this.Id = model.Id;
        this.AgentId = string.IsNullOrWhiteSpace(model.AgentId) ? null : model.AgentId;
        this.Role = model.Role;
        this.Content = text;
        this.Properties = new ReadOnlyDictionary<string, object>(model.Metadata);
    }

    private class Annotation : IAnnotation
    {
        public Annotation(string label, int startIndex, int endIndex, string fileId, string? quote)
        {
            this.FileId = fileId;
            this.Label = label;
            this.Quote = quote;
            this.StartIndex = startIndex;
            this.EndIndex = endIndex;
        }

        /// <inheritdoc/>
        public string FileId { get; }

        /// <inheritdoc/>
        public string Label { get; }

        /// <inheritdoc/>
        public string? Quote { get; }

        /// <inheritdoc/>
        public int StartIndex { get; }

        /// <inheritdoc/>
        public int EndIndex { get; }
    }
}
