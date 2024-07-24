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
    private readonly BedrockUtilities _util = new();
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
        var temperature = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature);
        var topP = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "p", (double?)DefaultTopP);
        var topK = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "k", (double?)DefaultTopK);
        var maxTokens = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", (int?)DefaultMaxTokens);
        var stopSequences = this._util.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stop_sequences", null);
        var returnLikelihoods = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "return_likelihoods", DefaultReturnLikelihoods);
        var stream = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "stream", (bool?)DefaultStream);
        var numGenerations = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "num_generations", (int?)DefaultNumGenerations);
        var logitBias = this._util.GetExtensionDataValue<Dictionary<int, double>>(executionSettings?.ExtensionData, "logit_bias", null);
        var truncate = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "truncate", DefaultTruncate);

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
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        throw new NotImplementedException();
    }
}
