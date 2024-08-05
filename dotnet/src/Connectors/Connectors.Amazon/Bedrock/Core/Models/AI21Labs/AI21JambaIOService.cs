// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Core;

/// <summary>
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
internal sealed class AI21JambaIOService : IBedrockModelIOService
{
    // Define constants for default values
    private const double DefaultTemperature = 1.0;
    private const double DefaultTopP = 0.9;
    private const int DefaultMaxTokens = 4096;
    private const int DefaultN = 1;
    private const double DefaultFrequencyPenalty = 0.0;
    private const double DefaultPresencePenalty = 0.0;

    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by AI21 Labs Jamba model.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var requestBody = new
        {
            messages = new[]
            {
                new
                {
                    role = "user",
                    content = prompt
                }
            },
            temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", DefaultTemperature),
            top_p = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", DefaultTopP),
            max_tokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            stop = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "stop", new List<string>()),
            n = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "n", DefaultN),
            frequency_penalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty),
            presence_penalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "presence_penalty", DefaultPresencePenalty)
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
        var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Choices is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Choices.Select(choice => new TextContent(choice.Message?.Content)));
        return textContents;
    }

    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by AI21 Labs Jamba.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []),
        };

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "n", DefaultN) },
                { "frequency_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
                { "presence_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) }
            },
            AdditionalModelResponseFieldPaths = []
        };

        return converseRequest;
    }
    /// <summary>
    /// Gets the streamed text output.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var buffer = new StringBuilder();
        if (chunk["choices"]?[0]?["delta"]?["content"] != null)
        {
            buffer.Append(chunk["choices"]?[0]?["delta"]?["content"]);
            yield return buffer.ToString();
        }
    }
    /// <summary>
    /// Gets converse stream output.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []),
        };

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "n", DefaultN) },
                { "frequency_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
                { "presence_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) }
            },
            AdditionalModelResponseFieldPaths = []
        };

        return converseRequest;
    }
}
