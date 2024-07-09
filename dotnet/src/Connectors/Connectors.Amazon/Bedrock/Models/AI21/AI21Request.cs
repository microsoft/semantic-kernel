// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.AI21;

public class AI21Request
{
    public class AI21ChatCompletionRequest : IChatCompletionRequest //for jamba
    {
        public List<Message> Messages { get; set; }
        public double Temperature { get; set; } = 1.0;
        public double TopP { get; set; } = 1.0;
        public int MaxTokens { get; set; } = 4096;
        public List<string> StopSequences { get; set; }
        public int NumResponses { get; set; } = 1;
        public double FrequencyPenalty { get; set; } = 0.0;
        public double PresencePenalty { get; set; } = 0.0;

        public List<SystemContentBlock> System { get; set; }
        public InferenceConfiguration InferenceConfig { get; set; }
        public Document AdditionalModelRequestFields { get; set; }
        public List<string> AdditionalModelResponseFieldPaths { get; set; }
        public GuardrailConfiguration GuardrailConfig { get; set; }
        public string ModelId { get; set; }
        public ToolConfiguration ToolConfig { get; set; }
    }

    [Serializable]
    public class AI21TextGenerationRequest : ITextGenerationRequest //for jamba
    {
        [JsonIgnore]
        public string InputText
        {
            get
            {
                // Concatenating the content of all messages to form the input text
                return string.Join(" ", Messages.Select(m => m.Content));
            }
        }
        [JsonPropertyName("messages")]
        public required List<Msg> Messages { get; set; }

        [JsonPropertyName("n")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? NumberOfResponses { get; set; }

        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        [JsonPropertyName("stop")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? Stop { get; set; }

        [JsonPropertyName("frequency_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? FrequencyPenalty { get; set; }

        [JsonPropertyName("presence_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? PresencePenalty { get; set; }

        int? ITextGenerationRequest.MaxTokens => MaxTokens;

        double? ITextGenerationRequest.TopP => TopP;

        double? ITextGenerationRequest.Temperature => Temperature;

        IList<string>? ITextGenerationRequest.StopSequences => Stop;
    }

    [Serializable]
    public class Msg
    {
        [JsonPropertyName("role")]
        public required string Role { get; set; }

        [JsonPropertyName("content")]
        public required string Content { get; set; }
    }
}
