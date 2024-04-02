// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class ClaudeRequest
{
    /// <summary>
    /// Input messages.<br/>
    /// Our models are trained to operate on alternating user and assistant conversational turns.
    /// When creating a new Message, you specify the prior conversational turns with the messages parameter,
    /// and the model then generates the next Message in the conversation.
    /// Each input message must be an object with a role and content. You can specify a single user-role message,
    /// or you can include multiple user and assistant messages. The first message must always use the user role.
    /// If the final message uses the assistant role, the response content will continue immediately
    /// from the content in that message. This can be used to constrain part of the model's response.
    /// </summary>
    [JsonPropertyName("messages")]
    public IList<Message> Messages { get; set; } = null!;

    [JsonPropertyName("model")]
    public string ModelId { get; set; } = null!;

    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; }

    /// <summary>
    /// A system prompt is a way of providing context and instructions to Claude, such as specifying a particular goal or persona.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("system")]
    public string? SystemPrompt { get; set; }

    /// <summary>
    /// Custom text sequences that will cause the model to stop generating.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("stop_sequences")]
    public IList<string>? StopSequences { get; set; }

    /// <summary>
    /// Enables SSE streaming.
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; }

    /// <summary>
    /// Amount of randomness injected into the response.<br/>
    /// Defaults to 1.0. Ranges from 0.0 to 1.0. Use temperature closer to 0.0 for analytical / multiple choice, and closer to 1.0 for creative and generative tasks.<br/>
    /// Note that even with temperature of 0.0, the results will not be fully deterministic.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }

    /// <summary>
    /// In nucleus sampling, we compute the cumulative distribution over all the options for each subsequent token
    /// in decreasing probability order and cut it off once it reaches a particular probability specified by top_p.
    /// You should either alter temperature or top_p, but not both.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("top_p")]
    public float? TopP { get; set; }

    /// <summary>
    /// Only sample from the top K options for each subsequent token.
    /// Used to remove "long tail" low probability responses.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonPropertyName("top_k")]
    public float? TopK { get; set; }

    internal sealed class Message
    {
        [JsonConverter(typeof(AuthorRoleConverter))]
        [JsonPropertyName("role")]
        public AuthorRole Role { get; set; }

        [JsonPropertyName("content")]
        public IList<ClaudeContent> Contents { get; set; } = null!;
    }
}
