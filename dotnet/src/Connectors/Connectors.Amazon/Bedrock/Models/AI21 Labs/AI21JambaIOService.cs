// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;

/// <summary>
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
public class AI21JambaIOService : IBedrockModelIOService
{
    private readonly BedrockModelUtilities _util = new();

    // Define constants for default values
    private const double DefaultTemperature = 1.0;
    private const double DefaultTopP = 0.9;
    private const int DefaultMaxTokens = 4096;
    private const int DefaultN = 1;
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by AI21 Labs Jamba model.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        List<AI21JambaRequest.Msg> messages = new()
        {
            new AI21JambaRequest.Msg
            {
                Role = "user",
                Content = prompt
            }
        };

        var temperature = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", DefaultTemperature);
        var topP = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", DefaultTopP);
        var maxTokens = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", DefaultMaxTokens);
        var stop = this._util.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stop", null);
        var numberOfResponses = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "n", DefaultN);
        var frequencyPenalty = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "frequency_penalty", (double?)null);
        var presencePenalty = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "presence_penalty", (double?)null);

        var requestBody = new AI21JambaRequest.AI21TextGenerationRequest
        {
            Messages = messages,
            Temperature = temperature,
            TopP = topP,
            MaxTokens = maxTokens,
            Stop = stop,
            NumberOfResponses = numberOfResponses,
            FrequencyPenalty = frequencyPenalty,
            PresencePenalty = presencePenalty
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
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Choices != null && responseBody.Choices.Count > 0)
                {
                    foreach (var choice in responseBody.Choices)
                    {
                        textContents.Add(new TextContent(choice.Message?.Content));
                    }
                }
                return textContents;
            }
        }
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
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            StopSequences = this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []),
        };

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = new List<SystemContentBlock>(),
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", this._util.GetExtensionDataValue(settings?.ExtensionData, "n", DefaultN) },
                { "frequency_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", 0.0) },
                { "presence_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", 0.0) }
            },
            AdditionalModelResponseFieldPaths = new List<string>()
        };

        return converseRequest;
    }
    /// <summary>
    /// Gets the streamed text output. AI21 Labs Jamba does not support streaming, but otherwise getting the text response body output would look like the following.
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
    /// AI21 Labs Jamba does not support streaming otherwise getting the converse stream output would look like the following (if model ever decides to add).
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            StopSequences = this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []),
        };

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = new List<SystemContentBlock>(),
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", this._util.GetExtensionDataValue(settings?.ExtensionData, "n", DefaultN) },
                { "frequency_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", 0.0) },
                { "presence_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", 0.0) }
            },
            AdditionalModelResponseFieldPaths = new List<string>()
        };

        return converseRequest;
    }
}
