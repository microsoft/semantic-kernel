// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized image content.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIImageContent : ImageContent
{
    /// <summary>
    /// Gets the metadata key for the detail level property.
    /// </summary>
    public const string DetailLevelProperty = nameof(DetailLevel);

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageContent"/> class.
    /// </summary>
    [JsonConstructor]
    public OpenAIImageContent()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageContent"/> class.
    /// </summary>
    /// <param name="uri">The URI of image.</param>
    public OpenAIImageContent(Uri uri) : base(uri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageContent"/> class.
    /// </summary>
    /// <param name="dataUri">DataUri of the image</param>
    public OpenAIImageContent(string dataUri) : base(dataUri)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIImageContent"/> class.
    /// </summary>
    /// <param name="data">Byte array of the image</param>
    /// <param name="mimeType">Mime type of the image</param>
    public OpenAIImageContent(ReadOnlyMemory<byte> data, string? mimeType) : base(data, mimeType)
    {
    }

    /// <summary>
    /// The level of detail with which the model should process the image and generate its textual understanding of it.
    /// More information here: <see href="https://platform.openai.com/docs/guides/vision/low-or-high-fidelity-image-understanding" />.
    /// </summary>
    public ChatImageDetailLevel? DetailLevel { get; set; }
}
