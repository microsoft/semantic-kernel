// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Anthropic;

public class ClaudeRequest
{
    public class ClaudeChatCompletionRequest : IChatCompletionRequest
    {
        public List<Message> Messages { get; set; }
        public List<SystemContentBlock> System { get; set; }
        public InferenceConfiguration InferenceConfig { get; set; }
        public Document AdditionalModelRequestFields { get; set; }
        public List<string> AdditionalModelResponseFieldPaths { get; set; }
        public GuardrailConfiguration GuardrailConfig { get; set; }
        public string ModelId { get; set; }
        public ToolConfiguration ToolConfig { get; set; }

        public string AnthropicVersion { get; set; }
        public List<ClaudeTool> Tools { get; set; }
        public ClaudeToolChoice ToolChoice { get; set; }

        public class ClaudeTool
        {
            public string Name { get; set; }
            public string Description { get; set; }
            public string InputSchema { get; set; }
        }

        public class ClaudeToolChoice
        {
            public string Type { get; set; }
            public string Name { get; set; }
        }
    }

    public class ClaudeTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }

        [JsonPropertyName("max_tokens_to_sample")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokensToSample { get; set; }

        [JsonPropertyName("stop_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

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

        double? ITextGenerationRequest.TopP => TopP;

        double? ITextGenerationRequest.Temperature => Temperature;

        int? ITextGenerationRequest.MaxTokens => MaxTokensToSample;

        IList<string>? ITextGenerationRequest.StopSequences => StopSequences;
    }
}
