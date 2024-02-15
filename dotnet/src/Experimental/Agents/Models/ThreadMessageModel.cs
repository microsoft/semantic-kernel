// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812
#pragma warning disable CA1852

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// list of run steps belonging to a run.
/// </summary>
internal sealed class ThreadMessageListModel : OpenAIListModel<ThreadMessageModel>
{
    // No specialization
}

/// <summary>
/// Represents a message within a thread.
/// </summary>
internal sealed class ThreadMessageModel
{
    /// <summary>
    /// Identifier, which can be referenced in API endpoints.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Unix timestamp (in seconds) for when the message was created.
    /// </summary>
    [JsonPropertyName("created_at")]
    public long CreatedAt { get; set; }

    /// <summary>
    /// The thread ID that this message belongs to.
    /// </summary>
    [JsonPropertyName("thread_id")]
    public string ThreadId { get; set; } = string.Empty;

    /// <summary>
    /// The entity that produced the message. One of "user" or "agent".
    /// </summary>
    [JsonPropertyName("role")]
    public string Role { get; set; } = string.Empty;

    /// <summary>
    /// The content of the message in array of text and/or images.
    /// </summary>
    [JsonPropertyName("content")]
    public List<ContentModel> Content { get; set; } = new List<ContentModel>();

    /// <summary>
    /// A list of file IDs that the agent should use.
    /// </summary>
    [JsonPropertyName("file_ids")]
    public List<string> FileIds { get; set; } = new List<string>();

    /// <summary>
    /// If applicable, the ID of the agent that authored this message.
    /// </summary>
    [JsonPropertyName("agent_id")]
    public string AgentId { get; set; } = string.Empty;

    /// <summary>
    /// If applicable, the ID of the run associated with the authoring of this message.
    /// </summary>
    [JsonPropertyName("run_id")]
    public string RunId { get; set; } = string.Empty;

    /// <summary>
    /// Set of 16 key-value pairs that can be attached to an object.
    /// This can be useful for storing additional information about the
    /// object in a structured format. Keys can be a maximum of 64
    /// characters long and values can be a maximum of 512 characters long.
    /// </summary>
    [JsonPropertyName("metadata")]
    public Dictionary<string, object> Metadata { get; set; } = new Dictionary<string, object>();

    /// <summary>
    /// Representa contents within a message.
    /// </summary>
    public sealed class ContentModel
    {
        /// <summary>
        /// Type of content.
        /// </summary>
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        /// <summary>
        /// Text context.
        /// </summary>
        [JsonPropertyName("text")]
        public TextContentModel? Text { get; set; }
    }

    /// <summary>
    /// Text content.
    /// </summary>
    public sealed class TextContentModel
    {
        /// <summary>
        /// The text itself.
        /// </summary>
        [JsonPropertyName("value")]
        public string Value { get; set; } = string.Empty;

        /// <summary>
        /// Any annotations on the text.
        /// </summary>
        [JsonPropertyName("annotations")]
        public List<TextAnnotationModel> Annotations { get; set; } = new List<TextAnnotationModel>();
    }

    public sealed class TextAnnotationModel
    {
        /// <summary>
        /// Type of content.
        /// </summary>
        [JsonPropertyName("type")]
        public string Type { get; set; } = string.Empty;

        /// <summary>
        /// The text of the citation-label text in the message content that can be replaced/reformatted.
        /// </summary>
        [JsonPropertyName("text")]
        public string Text { get; set; } = string.Empty;

        /// <summary>
        /// Annotation when type == "file_citation"
        /// </summary>
        [JsonPropertyName("file_citation")]
        public TextFileCitationModel? FileCitation { get; set; }

        /// <summary>
        /// Annotation when type == "file_path"
        /// </summary>
        [JsonPropertyName("file_path")]
        public TextFilePathModel? FilePath { get; set; }

        /// <summary>
        /// Start index of the citation.
        /// </summary>
        [JsonPropertyName("start_index")]
        public int StartIndex { get; set; }

        /// <summary>
        /// End index of the citation.
        /// </summary>
        [JsonPropertyName("end_index")]
        public int EndIndex { get; set; }
    }

    public sealed class TextFileCitationModel
    {
        /// <summary>
        /// The file identifier.
        /// </summary>
        [JsonPropertyName("file_id")]
        public string FileId { get; set; } = string.Empty;

        /// <summary>
        /// The citation.
        /// </summary>
        [JsonPropertyName("quote")]
        public string Quote { get; set; } = string.Empty;
    }

    public sealed class TextFilePathModel
    {
        /// <summary>
        /// The file identifier.
        /// </summary>
        [JsonPropertyName("file_id")]
        public string FileId { get; set; } = string.Empty;
    }
}
