// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Bedrock input-output service to build the request and response bodies as required by the given model.
/// </summary>
internal interface IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModelRequest Body parameter to be serialized. Object itself dependent on model request parameter requirements.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    internal object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null);

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API. Must be deserialized into the model's specific response object first.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object returned from the InvokeAsync Bedrock call. </param>
    /// <returns></returns>
    internal IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response);

    /// <summary>
    /// Builds the converse request given the chat history and model ID passed in by the user. This request is to be passed into the Bedrock Converse API call.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="chatHistory">The messages for the converse call.</param>
    /// <param name="settings">Optional prompt execution settings/</param>
    /// <returns></returns>
    internal ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null);

    /// <summary>
    /// Converts the Json output from the streaming text generation into IEnumerable strings for output.
    /// </summary>
    /// <param name="chunk">The payloadPart bytes outputted from the streaming response.</param>
    /// <returns></returns>
    internal IEnumerable<string> GetTextStreamOutput(JsonNode chunk);

    /// <summary>
    /// Builds the converse stream request given the chat history and model ID passed in by the user. This request is to be passed into the Bedrock Converse API call.
    /// </summary>
    /// <param name="modelId">The model ID for the request.</param>
    /// <param name="chatHistory">The ChatHistory object to be converted to messages for the stream converse request.</param>
    /// <param name="settings">PromptExecutionSettings for the request.</param>
    /// <returns></returns>
    internal ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null);
}
