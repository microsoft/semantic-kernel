// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Mistral;

public class MistralRequest
{
    [Serializable]
    public class MistralTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }

        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        [JsonPropertyName("stop")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; } = new List<string>();

        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        [JsonPropertyName("top_k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? TopK { get; set; }

        string ITextGenerationRequest.InputText => Prompt;
    }

    internal sealed class MistralChatCompletionRequest
    {
        [JsonPropertyName("model")]
        public string Model { get; set; }

        [JsonPropertyName("messages")]
        public IList<MistralChatMessage> Messages { get; set; } = [];

        [JsonPropertyName("temperature")]
        public double Temperature { get; set; } = 0.7;

        [JsonPropertyName("top_p")]
        public double TopP { get; set; } = 1;

        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        [JsonPropertyName("stream")]
        public bool Stream { get; set; } = false;

        [JsonPropertyName("safe_prompt")]
        public bool SafePrompt { get; set; } = false;

        [JsonPropertyName("tools")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<MistralTool>? Tools { get; set; }

        [JsonPropertyName("tool_choice")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? ToolChoice { get; set; }

        [JsonPropertyName("random_seed")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? RandomSeed { get; set; }

        /// <summary>
        /// Construct an instance of <see cref="ChatCompletionRequest"/>.
        /// </summary>
        /// <param name="model">ID of the model to use.</param>
        [JsonConstructor]
        internal MistralChatCompletionRequest(string model)
        {
            this.Model = model;
        }

        /// <summary>
        /// Add a tool to the request.
        /// </summary>
        internal void AddTool(MistralTool tool)
        {
            this.Tools ??= [];
            this.Tools.Add(tool);
        }

        /// <summary>
        /// Add a message to the request.
        /// </summary>
        /// <param name="message"></param>
        internal void AddMessage(MistralChatMessage message)
        {
            this.Messages.Add(message);
        }
    }
    public class MistralChatMessage : Message
    {
        [JsonPropertyName("role")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }

        [JsonPropertyName("tool_calls")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<MistralToolCall>? ToolCalls { get; set; }

        /// <summary>
        /// Construct an instance of <see cref="MistralChatMessage"/>.
        /// </summary>
        /// <param name="role">If provided must be one of: system, user, assistant</param>
        /// <param name="content">Content of the chat message</param>
        [JsonConstructor]
        internal MistralChatMessage(string? role, string? content)
        {
            if (role is not null and not "system" and not "user" and not "assistant" and not "tool")
            {
                throw new System.ArgumentException($"Role must be one of: system, user, assistant or tool. {role} is an invalid role.", nameof(role));
            }

            this.Role = role;
            this.Content = content;
        }
    }

    public class MistralToolCall
    {
        [JsonPropertyName("id")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Id { get; set; }

        [JsonPropertyName("function")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public MistralFunction? Function { get; set; }
    }
}
