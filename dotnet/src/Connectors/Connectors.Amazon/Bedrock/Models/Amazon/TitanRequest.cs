// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Amazon;

public class TitanRequest
{
    [Serializable]
    public class TitanTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("inputText")]
        public required string InputText { get; set; }

        [JsonPropertyName("textGenerationConfig")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public AmazonTitanTextGenerationConfig? TextGenerationConfig { get; set; }

        int? ITextGenerationRequest.MaxTokens => TextGenerationConfig?.MaxTokenCount;

        double? ITextGenerationRequest.TopP => TextGenerationConfig?.TopP;

        double? ITextGenerationRequest.Temperature => TextGenerationConfig?.Temperature;

        IList<string>? ITextGenerationRequest.StopSequences => TextGenerationConfig?.StopSequences;
    }

    public class AmazonTitanTextGenerationConfig
    {
        /// <summary>
        /// Top P controls token choices, based on the probability of the potential choices. The range is 0 to 1. The default is 1.
        /// </summary>
        [JsonPropertyName("topP")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        /// <summary>
        /// The Temperature value ranges from 0 to 1, with 0 being the most deterministic and 1 being the most creative.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        /// <summary>
        /// Configures the maximum number of tokens in the generated response. The range is 0 to 4096. The default is 512.
        /// </summary>
        [JsonPropertyName("maxTokenCount")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokenCount { get; set; }

        /// <summary>
        /// Use | (pipe) characters (maximum 20 characters).
        /// </summary>
        [JsonPropertyName("stopSequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; } = new List<string>();
    }

    public class TitanChatCompletionRequest : IChatCompletionRequest
    {
        public List<Message> Messages { get; set; }
        public List<SystemContentBlock> System { get; set; }
        public InferenceConfiguration InferenceConfig { get; set; }
        public Document AdditionalModelRequestFields { get; set; }
        public List<string> AdditionalModelResponseFieldPaths { get; set; }
        public GuardrailConfiguration GuardrailConfig { get; set; }
        public string ModelId { get; set; }
        public ToolConfiguration ToolConfig { get; set; }
    }
}
