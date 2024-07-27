// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
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
        var temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature);
        var topP = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "topP", (double?)DefaultTopP);
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "maxTokens", (int?)DefaultMaxTokens);
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stopSequences", null);
        var countPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicRequest.CountPenalty>(executionSettings?.ExtensionData, "countPenalty", null);
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicRequest.PresencePenalty>(executionSettings?.ExtensionData, "presencePenalty", null);
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicRequest.FrequencyPenalty>(executionSettings?.ExtensionData, "frequencyPenalty", null);

        var requestBody = new AI21JurassicRequest.AI21JurassicTextGenerationRequest()
        {
            Prompt = prompt,
            Temperature = temperature,
            TopP = topP,
            MaxTokens = maxTokens,
            StopSequences = stopSequences,
            CountPenalty = countPenalty,
            PresencePenalty = presencePenalty,
            FrequencyPenalty = frequencyPenalty
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
                var responseBody = JsonSerializer.Deserialize<AI21JurassicResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Completions != null && responseBody.Completions.Count > 0)
                {
                    foreach (var completion in responseBody.Completions)
                    {
                        textContents.Add(new TextContent(completion.Data?.Text));
                    }
                }

                return textContents;
            }
        }
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
        throw new NotImplementedException("Converse not supported by this model.");
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
