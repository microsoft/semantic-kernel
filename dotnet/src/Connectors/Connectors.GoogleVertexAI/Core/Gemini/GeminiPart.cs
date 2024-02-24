// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.GoogleVertexAI;

/// <summary>
/// Union field data can be only one of properties in class GeminiPart
/// </summary>
public sealed class GeminiPart : IJsonOnDeserialized
{
    /// <summary>
    /// Gets or sets the text data.
    /// </summary>
    [JsonPropertyName("text")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Text { get; set; }

    /// <summary>
    /// Gets or sets the image or video as binary data.
    /// </summary>
    [JsonPropertyName("inlineData")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public InlineDataPart? InlineData { get; set; }

    /// <summary>
    /// Gets or sets the image or video as file uri.
    /// </summary>
    [JsonPropertyName("fileData")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public FileDataPart? FileData { get; set; }

    /// <summary>
    /// Function call data.
    /// </summary>
    [JsonPropertyName("functionCall")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public FunctionCallPart? FunctionCall { get; set; }

    /// <summary>
    /// Object representing the function call response.
    /// </summary>
    [JsonPropertyName("functionResponse")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public FunctionResponsePart? FunctionResponse { get; set; }

    /// <summary>
    /// Checks whether only one property of the GeminiPart instance is not null.
    /// Returns true if only one property among Text, InlineData, FileData, FunctionCall, and FunctionResponse is not null,
    /// Otherwise, it returns false.
    /// </summary>
    public bool IsValid()
    {
        return (this.Text != null ? 1 : 0) +
            (this.InlineData != null ? 1 : 0) +
            (this.FileData != null ? 1 : 0) +
            (this.FunctionCall != null ? 1 : 0) +
            (this.FunctionResponse != null ? 1 : 0) == 1;
    }

    /// <inheritdoc />
    public void OnDeserialized()
    {
        if (!this.IsValid())
        {
            throw new JsonException(
                "GeminiPart is invalid. One and only one property among Text, InlineData, FileData, FunctionCall, and FunctionResponse should be set.");
        }
    }

    /// <summary>
    /// Inline media bytes like image or video data.
    /// </summary>
    public sealed class InlineDataPart
    {
        /// <summary>
        /// The IANA standard MIME type of the source data.
        /// </summary>
        /// <remarks>
        /// Acceptable values include: "image/png", "image/jpeg", "image/heic", "image/heif", "image/webp".
        /// </remarks>
        [JsonPropertyName("mimeType")]
        [JsonRequired]
        public string MimeType { get; set; } = null!;

        /// <summary>
        /// Base64 encoded data
        /// </summary>
        [JsonPropertyName("data")]
        [JsonRequired]
        public string InlineData { get; set; } = null!;
    }

    /// <summary>
    /// File media bytes like image or video data.
    /// </summary>
    public sealed class FileDataPart
    {
        /// <summary>
        /// The IANA standard MIME type of the source data.
        /// </summary>
        /// <remarks>
        /// Acceptable values include: "image/png", "image/jpeg", "video/mov", "video/mpeg", "video/mp4", "video/mpg", "video/avi", "video/wmv", "video/mpegps", "video/flv".
        /// </remarks>
        [JsonPropertyName("mimeType")]
        [JsonRequired]
        public string MimeType { get; set; } = null!;

        /// <summary>
        /// The Cloud Storage URI of the image or video to include in the prompt.
        /// The bucket that stores the file must be in the same Google Cloud project that's sending the request.
        /// </summary>
        [JsonPropertyName("fileUri")]
        [JsonRequired]
        public Uri FileUri { get; set; } = null!;
    }

    /// <summary>
    /// A predicted FunctionCall returned from the model that contains a
    /// string representing the FunctionDeclaration.name with the arguments and their values.
    /// </summary>
    public sealed class FunctionCallPart
    {
        /// <summary>
        /// Required. The name of the function to call. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 63.
        /// </summary>
        [JsonPropertyName("name")]
        [JsonRequired]
        public string FunctionName { get; set; } = null!;

        /// <summary>
        /// Optional. The function parameters and values in JSON object format.
        /// </summary>
        [JsonPropertyName("args")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public BinaryData? Arguments { get; set; }

        /// <inheritdoc />
        public override string ToString()
        {
            return $"FunctionName={this.FunctionName}, Arguments={this.Arguments}";
        }
    }

    /// <summary>
    /// The result output of a FunctionCall that contains a string representing the FunctionDeclaration.name and
    /// a structured JSON object containing any output from the function is used as context to the model.
    /// </summary>
    public sealed class FunctionResponsePart
    {
        /// <summary>
        /// Required. The name of the function to call. Must be a-z, A-Z, 0-9, or contain underscores and dashes, with a maximum length of 63.
        /// </summary>
        [JsonPropertyName("name")]
        [JsonRequired]
        public string FunctionName { get; set; } = null!;

        /// <summary>
        /// Required. The function response in JSON object format.
        /// </summary>
        [JsonPropertyName("response")]
        [JsonRequired]
        public IList<JsonNode> Response { get; set; } = null!;
    }
}
