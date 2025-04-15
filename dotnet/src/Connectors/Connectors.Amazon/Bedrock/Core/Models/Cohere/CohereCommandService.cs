// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Cohere Command.
/// </summary>
internal sealed class CohereCommandService : IBedrockTextGenerationService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonCommandExecutionSettings.FromExecutionSettings(executionSettings);
        var requestBody = new CommandRequest.CohereCommandTextGenerationRequest()
        {
            Prompt = prompt,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "temperature") ?? exec.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "p") ?? exec.TopP,
            TopK = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "k") ?? exec.TopK,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens") ?? exec.MaxTokens,
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(executionSettings?.ExtensionData, "stop_sequences") ?? exec.StopSequences,
            ReturnLikelihoods = BedrockModelUtilities.GetExtensionDataValue<string?>(executionSettings?.ExtensionData, "return_likelihoods") ?? exec.ReturnLikelihoods,
            Stream = BedrockModelUtilities.GetExtensionDataValue<bool?>(executionSettings?.ExtensionData, "stream") ?? exec.Stream,
            NumGenerations = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "num_generations") ?? exec.NumGenerations,
            LogitBias = BedrockModelUtilities.GetExtensionDataValue<Dictionary<int, double>?>(executionSettings?.ExtensionData, "logit_bias") ?? exec.LogitBias,
            Truncate = BedrockModelUtilities.GetExtensionDataValue<string?>(executionSettings?.ExtensionData, "truncate") ?? exec.Truncate
        };

        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<CommandResponse>(reader.ReadToEnd());

        if (responseBody?.Generations is not { Count: > 0 })
        {
            return [];
        }

        return responseBody.Generations
               .Where(g => !string.IsNullOrEmpty(g.Text))
               .Select(g => new TextContent(g.Text, innerContent: responseBody))
               .ToList();
    }

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        var generations = chunk["generations"]?.AsArray();
        if (generations != null)
        {
            foreach (var generation in generations)
            {
                var text = generation?["text"]?.ToString();
                if (!string.IsNullOrEmpty(text))
                {
                    yield return new StreamingTextContent(text, innerContent: chunk)!;
                }
            }
        }
    }
}
