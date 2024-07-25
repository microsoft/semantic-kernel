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
    private readonly BedrockModelUtilities _util = new();

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
        var temperature = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature);
        var topP = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", (double?)DefaultTopP);
        var maxGenLen = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "max_gen_len", (int?)DefaultMaxGenLen);

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
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_gen_len", DefaultMaxGenLen)
        };

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = new List<SystemContentBlock>(),
            InferenceConfig = inferenceConfig,
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
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockModelUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "top_p", (float)DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_gen_len", DefaultMaxGenLen)
        };

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = new List<SystemContentBlock>(),
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };

        return converseRequest;
    }
}
