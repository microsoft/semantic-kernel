// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.AI21;

public class AI21Request
{
    public class AI21ChatCompletionRequest : IChatCompletionRequest
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
}
