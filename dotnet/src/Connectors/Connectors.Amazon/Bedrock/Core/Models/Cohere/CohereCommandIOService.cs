// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Cohere Command.
/// </summary>
internal sealed class CohereCommandIOService : IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    object IBedrockModelIOService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
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

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns>A list of text content objects as required by the semantic kernel.</returns>
    IReadOnlyList<TextContent> IBedrockModelIOService.GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<CommandResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Generations is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(from generation in responseBody.Generations where !string.IsNullOrEmpty(generation.Text) select new TextContent(generation.Text));
        return textContents;
    }

    /// <summary>
    /// Extracts the text generation streaming output from the Cohere Command response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    IEnumerable<string> IBedrockModelIOService.GetTextStreamOutput(JsonNode chunk)
    {
        var generations = chunk["generations"]?.AsArray();
        if (generations != null)
        {
            foreach (var generation in generations)
            {
                var text = generation?["text"]?.ToString();
                if (!string.IsNullOrEmpty(text))
                {
                    yield return text;
                }
            }
        }
    }

    /// <summary>
    /// Command does not support Converse (only Command R): "Limited. No chat support." - https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html#conversation-inference-supported-models-features
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    ConverseRequest IBedrockModelIOService.GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        throw new NotImplementedException("Converse not supported by this model.");
    }

    /// <summary>
    /// Command does not support ConverseStream (only Command R): "Limited. No chat support." - https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html#conversation-inference-supported-models-features
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    /// <exception cref="NotImplementedException"></exception>
    ConverseStreamRequest IBedrockModelIOService.GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        throw new NotImplementedException("Streaming not supported by this model.");
    }
}
