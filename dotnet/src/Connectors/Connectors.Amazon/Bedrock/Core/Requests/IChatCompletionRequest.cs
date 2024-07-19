// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
namespace Connectors.Amazon.Core.Requests;

/// <summary>
/// Request object for chat completion, essentially a ConverseRequest.
/// </summary>
public interface IChatCompletionRequest
{
    /// <summary>
    /// List of Messages from Chat History.
    /// </summary>
    public List<Message>? Messages { get; set; }
    /// <summary>
    /// System configurations.
    /// </summary>
    public List<SystemContentBlock>? System { get; set; }
    /// <summary>
    /// Model inference configurations which have base parameters: maxTokens, stopSequence, topP, and temperature.
    /// </summary>
    public InferenceConfiguration? InferenceConfig { get; set; }
    /// <summary>
    /// Any other additional model request parameters.
    /// </summary>
    public Document AdditionalModelRequestFields { get; set; }
    /// <summary>
    /// Additional fields for model response.
    /// </summary>
    public List<string>? AdditionalModelResponseFieldPaths { get; set; }
    /// <summary>
    /// Configuration information for a guardrail that you want to use in the request.
    /// </summary>
    public GuardrailConfiguration? GuardrailConfig { get; set; }
    /// <summary>
    /// Model ID as passed in by user.
    /// </summary>
    public string? ModelId { get; set; }
    /// <summary>
    /// Configuration information for the tools that the model can use when generating a response. This field is only supported by Anthropic Claude 3, Cohere Command R, Cohere Command R+, and Mistral Large models.
    /// </summary>
    public ToolConfiguration? ToolConfig { get; set; }
}
