// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Cohere;

/// <summary>
/// Input-output service for Cohere Command.
/// </summary>
public class CohereCommandIOService : IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command.
    /// </summary>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings? executionSettings = null)
    {
        double? temperature = 0.9; // Cohere default
        double? topP = 0.75; // Cohere default
        int? maxTokens = 20; // Cohere default
        List<string>? stopSequences = null;
        double? topK = 0; // Cohere default
        string? returnLikelihoods = "NONE"; // Cohere default
        bool? stream = false; // Cohere default
        int? numGenerations = 1; // Cohere default
        Dictionary<int, double>? logitBias = null;
        string? truncate = "END"; // Cohere default

        if (executionSettings is { ExtensionData: not null })
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("k", out var topKValue);
            topK = topKValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens", out var maxTokensValue);
            maxTokens = maxTokensValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop_sequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("return_likelihoods", out var returnLikelihoodsValue);
            returnLikelihoods = returnLikelihoodsValue as string;

            executionSettings.ExtensionData.TryGetValue("stream", out var streamValue);
            stream = streamValue as bool?;

            executionSettings.ExtensionData.TryGetValue("num_generations", out var numGenerationsValue);
            numGenerations = numGenerationsValue as int?;

            executionSettings.ExtensionData.TryGetValue("logit_bias", out var logitBiasValue);
            logitBias = logitBiasValue as Dictionary<int, double>;

            executionSettings.ExtensionData.TryGetValue("truncate", out var truncateValue);
            truncate = truncateValue as string;
        }

        var requestBody = new CommandTextRequest.CohereCommandTextGenerationRequest
        {
            Prompt = prompt,
            Temperature = temperature,
            TopP = topP,
            TopK = topK,
            MaxTokens = maxTokens,
            StopSequences = stopSequences,
            ReturnLikelihoods = returnLikelihoods,
            Stream = stream,
            NumGenerations = numGenerations,
            LogitBias = logitBias,
            Truncate = truncate
        };

        return requestBody;
    }
    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns>A list of text content objects as required by the semantic kernel.</returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<CommandTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Generations != null && responseBody.Generations.Count > 0)
                {
                    foreach (var generation in responseBody.Generations)
                    {
                        if (!string.IsNullOrEmpty(generation.Text))
                        {
                            textContents.Add(new TextContent(generation.Text));
                        }
                    }
                }
                return textContents;
            }
        }
    }
    /// <summary>
    /// Extracts the text generation streaming output from the Cohere Command response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
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
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException();
    }
    /// <summary>
    /// Command does not support ConverseStream (only Command R): "Limited. No chat support." - https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html#conversation-inference-supported-models-features
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
