// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
namespace Connectors.Amazon.Core.Requests;

public interface IChatCompletionRequest //essentially a ConverseRequest
{
    public List<Message> Messages { get; set; }
    public List<SystemContentBlock> System { get; set; }
    public InferenceConfiguration InferenceConfig { get; set; }
    public Dictionary<string, object> AdditionalModelRequestFields { get; set; }
    public List<string> AdditionalModelResponseFieldPaths { get; set; }
    public GuardrailConfiguration GuardrailConfig { get; set; }
}
