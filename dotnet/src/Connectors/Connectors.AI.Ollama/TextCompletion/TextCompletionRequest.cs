// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

/// <summary>
/// HTTP schema to perform completion request.
/// See https://github.com/jmorganca/ollama/blob/main/docs/api.md#parameters
/// </summary>
[Serializable]
public sealed class TextCompletionRequest
{
    /// <summary>
    /// Model name.
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;

    /// <summary>
    /// The prompt to generate a response for.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// The format to return a response in. Currently the only accepted value is json.
    /// </summary>
    [JsonPropertyName("format")]
    public string Format { get; set; } = string.Empty;

    /// <summary>
    /// Additional model parameters listed in the documentation for the Modelfile such as temperature
    /// </summary>
    [JsonPropertyName("options")]
    public Dictionary<string, object>? Options { get; set; };

    /// <summary>
    /// System prompt to (overrides what is defined in the Modelfile)
    /// </summary>
    [JsonPropertyName("system")]
    public string? System { get; set; }

    /// <summary>
    /// The full prompt or prompt template (overrides what is defined in the Modelfile)
    /// </summary>
    [JsonPropertyName("template")]
    public string? Template { get; set; }

    /// <summary>
    /// The context parameter returned from a previous request to /generate, this can be used to keep a short conversational memory
    /// </summary>
    [JsonPropertyName("context")]
    public string? Context { get; set; }

    /// <summary>
    /// If false the response will be returned as a single response object, rather than a stream of objects
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; }

    /// <summary>
    /// If true no formatting will be applied to the prompt and no context will be returned.
    /// You may choose to use the raw parameter if you are specifying a full templated prompt in your request to the API, and are managing history yourself.
    /// </summary>
    [JsonPropertyName("raw")]
    public bool Raw { get; set; } = true;
}
