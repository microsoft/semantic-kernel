// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models;

public interface IBedrockModelIOService<TRequest, TResponse>
{
    object GetInvokeModelRequestBody(string text, PromptExecutionSettings settings);
    IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response);
    ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null);
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk);
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings);
}
