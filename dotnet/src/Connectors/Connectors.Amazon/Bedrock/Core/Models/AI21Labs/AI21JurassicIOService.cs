// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for AI21 Labs Jurassic.
/// </summary>
internal sealed class AI21JurassicIOService : IBedrockTextGenerationIOService
{
    /// <summary>
    /// Builds InvokeModelRequest Body parameter to be serialized.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    object IBedrockTextGenerationIOService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonJurassicExecutionSettings.FromExecutionSettings(executionSettings);
        var requestBody = new AI21JurassicRequest.AI21JurassicTextGenerationRequest
        {
            Prompt = prompt,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? exec.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "topP") ?? exec.TopP,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "maxTokens") ?? exec.MaxTokens,
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stopSequences") ?? exec.StopSequences,
            CountPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "countPenalty") ?? exec.CountPenalty,
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "presencePenalty") ?? exec.PresencePenalty,
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "frequencyPenalty") ?? exec.FrequencyPenalty
        };
        return requestBody;
    }

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns></returns>
    IReadOnlyList<TextContent> IBedrockTextGenerationIOService.GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<AI21JurassicResponse>(reader.ReadToEnd());
        List<TextContent> textContents = [];
        if (responseBody?.Completions is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Completions.Select(completion => new TextContent(completion.Data?.Text)));
        return textContents;
    }

    /// <summary>
    /// Jurassic does not support streaming.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    IEnumerable<string> IBedrockTextGenerationIOService.GetTextStreamOutput(JsonNode chunk)
    {
        throw new NotSupportedException("Streaming not supported by this model.");
    }
}
