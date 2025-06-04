// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// The Amazon Titan Text response object when deserialized from Invoke Model call.
/// </summary>
internal sealed class EmbedResponse
{
    /// <summary>
    /// The number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("inputTextTokenCount")]
    public int InputTextTokenCount { get; set; }

    /// <summary>
    /// The provided input text strings for text embedding response.
    /// </summary>
    [JsonPropertyName("texts")]
    public IList<string>? Texts { get; set; }

    /// <summary>
    /// A list containing float arrays of the embeddings for each text string.
    /// </summary>
    [JsonPropertyName("embeddings")]
    public IList<IList<float>?>? Embeddings { get; set; }
}
