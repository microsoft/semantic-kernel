// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
namespace Connectors.Amazon.Core.Requests;

public interface IChatCompletionRequest
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
