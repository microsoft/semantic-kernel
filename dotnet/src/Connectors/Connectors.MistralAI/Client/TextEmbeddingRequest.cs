// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Request for text embedding.
/// </summary>
internal sealed class TextEmbeddingRequest
{
    [JsonPropertyName("model")]
    public string Model { get; set; }

    [JsonPropertyName("input")]
    public IList<string> Input { get; set; }

    [JsonPropertyName("encoding_format")]
    public string EncodingFormat { get; set; }

    /// <summary>
    /// Construct an instance of <see cref="TextEmbeddingRequest"/>.
    /// </summary>
    /// <param name="model">ID of the model to use.</param>
    /// <param name="input">The list of strings to embed.</param>
    /// <param name="encodingFormat">The format of the output data.</param>
    internal TextEmbeddingRequest(string model, IList<string> input, string? encodingFormat = null)
    {
        this.Model = model;
        this.Input = input;
        this.EncodingFormat = encodingFormat ?? "float";
    }
}
