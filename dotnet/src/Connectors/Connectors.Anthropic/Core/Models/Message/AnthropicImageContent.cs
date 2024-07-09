// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class AnthropicImageContent : AnthropicContent
{
    /// <summary>
    /// Only used when type is "image". The image content.
    /// </summary>
    [JsonPropertyName("source")]
    public SourceEntity Source { get; set; } = null!;

    internal sealed class SourceEntity
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
