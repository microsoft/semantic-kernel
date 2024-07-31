// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;

/// <summary>
/// Input-output service for AI21 Labs Jurassic.
/// </summary>
public class AI21JurassicIOService : IBedrockModelIOService
{
    // Defined constants for default values
    private const double DefaultTemperature = 0.5;
    private const double DefaultTopP = 0.5;
    private const int DefaultMaxTokens = 200;
    /// <summary>
    /// Builds InvokeModelRequest Body parameter to be serialized.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var requestBody = new
        {
            prompt,
            temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature),
            topP = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "topP", (double?)DefaultTopP),
            maxTokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "maxTokens", (int?)DefaultMaxTokens),
            stopSequences = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "stopSequences", new List<string>()),
            countPenalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "countPenalty", new Dictionary<string, object>()),
            presencePenalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "presencePenalty", new Dictionary<string, object>()),
            frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "frequencyPenalty", new Dictionary<string, object>())
        };

        return requestBody;
    }
    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns></returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<AI21JurassicResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Completions is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Completions.Select(completion => new TextContent(completion.Data?.Text)));
        return textContents;
    }
    /// <summary>
    /// Jurassic does not support converse.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException("This model does not support chat history. Use text generation to invoke singular response to use this model.");
    }
    /// <summary>
    /// Jurassic does not support streaming.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        throw new NotImplementedException("Streaming not supported by this model.");
    }
    /// <summary>
    /// Jurassic does not support converse (or streaming for that matter).
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException("Streaming not supported by this model.");
    }
}
