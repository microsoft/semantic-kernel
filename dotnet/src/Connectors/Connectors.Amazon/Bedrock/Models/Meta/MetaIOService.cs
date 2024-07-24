// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Meta;

/// <summary>
/// Input-output service for Meta Llama.
/// </summary>
public class MetaIOService : IBedrockModelIOService
{
    private readonly BedrockUtilities _util = new();

    // Define constants for default values
    private const double DefaultTemperature = 0.5;
    private const double DefaultTopP = 0.9;
    private const int DefaultMaxGenLen = 512;
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Meta Llama.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        double? temperature = DefaultTemperature;
        double? topP = DefaultTopP;
        int? maxGenLen = DefaultMaxGenLen;

        if (executionSettings is { ExtensionData: not null })
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("top_p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_gen_len", out var maxGenLenValue);
            maxGenLen = maxGenLenValue as int?;
        }

        var requestBody = new LlamaTextRequest.LlamaTextGenerationRequest
        {
            Prompt = prompt,
            Temperature = temperature,
            TopP = topP,
            MaxGenLen = maxGenLen
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
                var responseBody = JsonSerializer.Deserialize<LlamaTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (!string.IsNullOrEmpty(responseBody?.Generation))
                {
                    textContents.Add(new TextContent(responseBody.Generation));
                }

                return textContents;
            }
        }
    }
    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by Meta Llama.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var llamaRequest = new LlamaChatRequest()
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxGenLen = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_gen_len", DefaultMaxGenLen)
        };
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = llamaRequest.Messages,
            System = llamaRequest.System,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = llamaRequest.Temperature,
                TopP = llamaRequest.TopP,
                MaxTokens = llamaRequest.MaxGenLen
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };
        return converseRequest;
    }
    /// <summary>
    /// Extracts the text generation streaming output from the Meta Llama response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var generation = chunk["generation"]?.ToString();
        if (!string.IsNullOrEmpty(generation))
        {
            yield return generation;
        }
    }

    /// <summary>
    /// Builds the ConverseStreamRequest object for the Converse Bedrock API call, including building the Meta Llama Request object and mapping parameters to the ConverseStreamRequest object.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(
        string modelId,
        ChatHistory chatHistory,
        PromptExecutionSettings? settings = null)
    {
        var llamaRequest = new LlamaChatRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxGenLen = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_gen_len", DefaultMaxGenLen)
        };
        var converseStreamRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = llamaRequest.Messages,
            System = llamaRequest.System,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = llamaRequest.Temperature,
                TopP = llamaRequest.TopP,
                MaxTokens = llamaRequest.MaxGenLen
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };
        return converseStreamRequest;
    }
}
