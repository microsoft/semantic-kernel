// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Text generation response object for Meta Llama.
/// </summary>
internal sealed class LlamaResponse
{
    /// <summary>
    /// The generated text.
    /// </summary>
    [JsonPropertyName("generation")]
    public string? Generation { get; set; }

    /// <summary>
    /// The number of tokens in the prompt.
    /// </summary>
    [JsonPropertyName("prompt_token_count")]
    public int PromptTokenCount { get; set; }

    /// <summary>
    /// The number of tokens in the generated text.
    /// </summary>
    [JsonPropertyName("generation_token_count")]
    public int GenerationTokenCount { get; set; }

    /// <summary>
    /// The reason why the response stopped generating text. Possible values are stop (The model has finished generating text for the input prompt) and length (The length of the tokens for the generated text exceeds the value of max_gen_len in the call to InvokeModel (InvokeModelWithResponseStream, if you are streaming output). The response is truncated to max_gen_len tokens. Consider increasing the value of max_gen_len and trying again.).
    /// </summary>
    [JsonPropertyName("stop_reason")]
    public string? StopReason { get; set; }
}
