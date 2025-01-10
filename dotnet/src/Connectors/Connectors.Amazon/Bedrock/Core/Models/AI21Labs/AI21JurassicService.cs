// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for AI21 Labs Jurassic.
/// </summary>
internal sealed class AI21JurassicService : IBedrockTextGenerationService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var settings = AmazonJurassicExecutionSettings.FromExecutionSettings(executionSettings);
        var requestBody = new AI21JurassicRequest.AI21JurassicTextGenerationRequest
        {
            Prompt = prompt,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? settings.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "topP") ?? settings.TopP,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "maxTokens") ?? settings.MaxTokens,
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stopSequences") ?? settings.StopSequences,
            CountPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "countPenalty") ?? settings.CountPenalty,
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "presencePenalty") ?? settings.PresencePenalty,
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<AI21JurassicPenalties?>(executionSettings?.ExtensionData, "frequencyPenalty") ?? settings.FrequencyPenalty
        };
        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<AI21JurassicResponse>(reader.ReadToEnd());

        if (responseBody?.Completions is not { Count: > 0 })
        {
            return [];
        }

        return responseBody.Completions
            .Select(completion => new TextContent(completion.Data?.Text, innerContent: responseBody))
            .ToList();
    }

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        throw new NotSupportedException("Streaming not supported by this model.");
    }
}
