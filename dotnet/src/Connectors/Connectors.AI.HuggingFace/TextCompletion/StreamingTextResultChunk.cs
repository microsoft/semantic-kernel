// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

/// <summary>
/// StreamResponse class in <see href="https://github.com/huggingface/text-generation-inference/tree/main/clients/python"></see>
/// </summary>
public class StreamingTextResultChunk : StreamingContent
{
    /// <inheritdoc/>
    public override string Type { get; }

    /// <inheritdoc/>
    public override int ChoiceIndex { get; }

    /// <summary>
    /// Complete generated text
    /// Only available when the generation is finished
    /// </summary>
    public string? GeneratedText { get; set; }

    /// <summary>
    /// Optional Generation details
    /// Only available when the generation is finished
    /// </summary>
    public string? Details { get; set; }

    /// <summary>
    /// Token details
    /// </summary>
    public TokenChunkModel Token { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="StreamingTextResultChunk"/> class.
    /// </summary>
    /// <param name="type">Type of the chunk</param>
    /// <param name="jsonChunk">JsonElement representation of the chunk</param>
    public StreamingTextResultChunk(string type, JsonElement jsonChunk) : base(jsonChunk)
    {
        this.Type = type;
        this.ChoiceIndex = 0;
        this.GeneratedText = jsonChunk.GetProperty("generated_text").GetString();
        this.Details = jsonChunk.GetProperty("details").GetString();
        this.Token = JsonSerializer.Deserialize<TokenChunkModel>(jsonChunk.GetProperty("token").GetRawText())!;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Token?.Text ?? string.Empty;
    }

    /// <summary>
    /// Token class in <see href="https://github.com/huggingface/text-generation-inference/tree/main/clients/python"></see>
    /// </summary>
    public record TokenChunkModel
    {
        /// <summary>
        /// Id of the token
        /// </summary>
        [JsonPropertyName("id")]
        public int Id { get; set; }

        /// <summary>
        /// Text associated to the Token
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// Log probability of the token
        /// </summary>
        [JsonPropertyName("logprob")]
        public decimal LogProb { get; set; }

        /// <summary>
        /// Is the token a special token?
        /// Can be used to ignore tokens when concatenating
        /// </summary>
        [JsonPropertyName("special")]
        public bool Special { get; set; }
    }
}
