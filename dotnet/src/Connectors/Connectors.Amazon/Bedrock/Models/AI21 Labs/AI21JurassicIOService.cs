// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;

/// <summary>
/// Input-output service for AI21 Labs Jurassic.
/// </summary>
public class AI21JurassicIOService : IBedrockModelIOService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIOService<ITextGenerationRequest, ITextGenerationResponse>
{
    /// <summary>
    /// Builds InvokeModelRequest Body parameter to be serialized.
    /// </summary>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings? executionSettings = null)
    {
        double? temperature = 0.5; // AI21 Jurassic default
        double? topP = 0.5; // AI21 Jurassic default
        int? maxTokens = 200; // AI21 Jurassic default
        List<string>? stopSequences = null;
        AI21JurassicRequest.CountPenalty? countPenalty = null;
        AI21JurassicRequest.PresencePenalty? presencePenalty = null;
        AI21JurassicRequest.FrequencyPenalty? frequencyPenalty = null;

        if (executionSettings is { ExtensionData: not null })
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("topP", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("maxTokens", out var maxTokensValue);
            maxTokens = maxTokensValue as int?;

            executionSettings.ExtensionData.TryGetValue("stopSequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("countPenalty", out var countPenaltyValue);
            countPenalty = countPenaltyValue as AI21JurassicRequest.CountPenalty;

            executionSettings.ExtensionData.TryGetValue("presencePenalty", out var presencePenaltyValue);
            presencePenalty = presencePenaltyValue as AI21JurassicRequest.PresencePenalty;

            executionSettings.ExtensionData.TryGetValue("frequencyPenalty", out var frequencyPenaltyValue);
            frequencyPenalty = frequencyPenaltyValue as AI21JurassicRequest.FrequencyPenalty;
        }

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
        throw new NotImplementedException();
    }
    /// <summary>
    /// Jurassic does not support streaming.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        throw new NotImplementedException();
    }
    /// <summary>
    /// Jurassic does not support converse (or streaming for that matter).
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        throw new NotImplementedException();
    }
}
