// Copyright (c) Microsoft. All rights reserved.

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
}
