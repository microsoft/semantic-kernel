// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
internal sealed class ClaudeMessageContent
{
    /// <summary>
    /// Type of content. Possible values are "text" and "image".
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("type")]
    public string Type { get; set; } = null!;

    /// <summary>
    /// Only used when type is "text". The text content.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("text")]
    public string? Text { get; set; }

    /// <summary>
    /// Only used when type is "image". The image content.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("source")]
    public SourceEntity? Image { get; set; }

    internal sealed class SourceEntity
    {
        [JsonConstructor]
        internal SourceEntity(string type, string mediaType, string data)
        {
            this.Type = type;
            this.MediaType = mediaType;
            this.Data = data;
        }

        /// <summary>
        /// Currently supported only base64.
        /// </summary>
        [JsonPropertyName("type")]
        public string Type { get; set; }

        /// <summary>
        /// The media type of the image.
        /// </summary>
        [JsonPropertyName("media_type")]
        public string MediaType { get; set; }

        /// <summary>
        /// The base64 encoded image data.
        /// </summary>
        [JsonPropertyName("data")]
        public string Data { get; set; }
    }
}
