// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Cohere Command.
/// </summary>
internal sealed class CohereCommandIOService : IBedrockModelIOService
{
    // Define constants for default values
    private const double DefaultTemperature = 0.9;
    private const double DefaultTopP = 0.75;
    private const int DefaultMaxTokens = 20;
    private const double DefaultTopK = 0.0;
    private const string DefaultReturnLikelihoods = "NONE";
    private const bool DefaultStream = false;
    private const int DefaultNumGenerations = 1;
    private const string DefaultTruncate = "END";
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var requestBody = new
        {
            prompt,
            temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature),
            p = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "p", (double?)DefaultTopP),
            k = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "k", (double?)DefaultTopK),
            max_tokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", (int?)DefaultMaxTokens),
            stop_sequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stop_sequences", []),
            return_likelihoods = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "return_likelihoods", DefaultReturnLikelihoods),
            stream = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "stream", (bool?)DefaultStream),
            num_generations = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "num_generations", (int?)DefaultNumGenerations),
            logit_bias = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "logit_bias", new Dictionary<int, double>()),
            truncate = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "truncate", DefaultTruncate)
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
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<CommandTextResponse>(reader.ReadToEnd());
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
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException("Streaming not supported by this model.");
    }
}
