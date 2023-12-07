// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image response
/// </summary>
[Experimental("SKEXP0012")]
public class TextToImageResponse
{
    /// <summary>
    /// OpenAI Image response
    /// </summary>
    public sealed class Image
    {
        /// <summary>
        /// URL to the image created
        /// </summary>
        [JsonPropertyName("url")]
        [SuppressMessage("Design", "CA1056:URI return values should not be strings", Justification = "Using the original value")]
        public string Url { get; set; } = string.Empty;

        /// <summary>
        /// Image content in base64 format
        /// </summary>
        [JsonPropertyName("b64_json")]
        public string AsBase64 { get; set; } = string.Empty;
    }

    /// <summary>
    /// List of possible images
    /// </summary>
    [JsonPropertyName("data")]
    public IList<Image> Images { get; set; } = new List<Image>();

    /// <summary>
    /// Creation time
    /// </summary>
    [JsonPropertyName("created")]
    public int CreatedTime { get; set; }
}
