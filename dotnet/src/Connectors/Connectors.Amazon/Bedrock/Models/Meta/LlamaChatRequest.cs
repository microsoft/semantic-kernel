// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Meta;

/// <summary>
/// Meta Llama chat completion request body.
/// </summary>
public class LlamaChatRequest : IChatCompletionRequest
{
    /// <summary>
    /// (Required) The prompt that you want to pass to the model.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string? Prompt { get; set; }
    /// <summary>
    /// Use a lower value to decrease randomness in the response.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float Temperature { get; set; }
    /// <summary>
    /// Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable.
    /// </summary>
    [JsonPropertyName("top_p")]
    public float TopP { get; set; }
    /// <summary>
    /// Specify the maximum number of tokens to use in the generated response. The model truncates the response once the generated text exceeds max_gen_len.
    /// </summary>
    [JsonPropertyName("max_gen_len")]
    public int MaxGenLen { get; set; }

    /// <inheritdoc />
    public List<Message>? Messages { get; set; }
    /// <inheritdoc />
    public List<SystemContentBlock>? System { get; set; }
    /// <inheritdoc />
    public InferenceConfiguration? InferenceConfig { get; set; }
    /// <inheritdoc />
    public Document AdditionalModelRequestFields { get; set; }
    /// <inheritdoc />
    public List<string>? AdditionalModelResponseFieldPaths { get; set; }
    /// <inheritdoc />
    public GuardrailConfiguration? GuardrailConfig { get; set; }
    /// <inheritdoc />
    public string? ModelId { get; set; }
    /// <inheritdoc />
    public ToolConfiguration? ToolConfig { get; set; }
}
