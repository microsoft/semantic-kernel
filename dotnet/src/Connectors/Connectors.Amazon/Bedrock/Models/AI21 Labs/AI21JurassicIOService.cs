// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;

public class AI21JurassicIOService : IBedrockModelIOService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIOService<ITextGenerationRequest, ITextGenerationResponse>
{
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        double? temperature = 0.5; // AI21 Jurassic default
        double? topP = 0.5; // AI21 Jurassic default
        int? maxTokens = 200; // AI21 Jurassic default
        List<string>? stopSequences = null;
        AI21JurassicRequest.CountPenalty? countPenalty = null;
        AI21JurassicRequest.PresencePenalty? presencePenalty = null;
        AI21JurassicRequest.FrequencyPenalty? frequencyPenalty = null;

        if (executionSettings != null && executionSettings.ExtensionData != null)
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
                        if (completion.Data != null)
                        {
                            textContents.Add(new TextContent(completion.Data.Text));
                        }
                    }
                }

                return textContents;
            }
        }
    }
    // Jurassic does not support converse.
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException();
    }

    // Jurassic does not support streaming.
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        throw new NotImplementedException();
    }

    // Jurassic does not support converse (or streaming for that matter).
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        throw new NotImplementedException();
    }
}
