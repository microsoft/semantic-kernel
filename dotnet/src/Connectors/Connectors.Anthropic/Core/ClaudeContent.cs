// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Claude.
/// </summary>
internal sealed class ClaudeContent
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
    public ImageContent? Image { get; set; }

    internal sealed class ImageContent
    {
        /// <summary>
        /// Currently supported only base64.
        /// </summary>
        [JsonPropertyName("type")]
        public string Type { get; set; } = null!;

        /// <summary>
        /// The media type of the image.
        /// </summary>
        [JsonPropertyName("media_type")]
        public string MediaType { get; set; } = null!;

        /// <summary>
        /// The base64 encoded image data.
        /// </summary>
        [JsonPropertyName("data")]
        public string Data { get; set; } = null!;
    }
}
