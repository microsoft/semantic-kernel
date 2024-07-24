// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Cohere;

/// <summary>
/// Input-output service for Cohere Command R.
/// </summary>
public class CohereCommandRIOService : IBedrockModelIOService
{
    private readonly BedrockUtilities _util = new();

    // Define constants for default values
    private const float DefaultTemperature = 0.3f;
    private const float DefaultTopP = 0.75f;
    private const float DefaultTopK = 0.0f;
    private const string DefaultPromptTruncation = "OFF";
    private const float DefaultFrequencyPenalty = 0.0f;
    private const float DefaultPresencePenalty = 0.0f;
    private const int DefaultSeed = 0;
    private const bool DefaultReturnPrompt = false;
    private const bool DefaultRawPrompting = false;
    private const int DefaultMaxTokens = 4096;
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command R.
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
        var promptTruncation = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation);
        var frequencyPenalty = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "frequency_penalty", (double?)DefaultFrequencyPenalty);
        var presencePenalty = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "presence_penalty", (double?)DefaultPresencePenalty);
        var seed = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "seed", (int?)DefaultSeed);
        var returnPrompt = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "return_prompt", (bool?)DefaultReturnPrompt);
        var tools = this._util.GetExtensionDataValue<List<CommandRTextRequest.Tool>>(executionSettings?.ExtensionData, "tools", null);
        var toolResults = this._util.GetExtensionDataValue<List<CommandRTextRequest.ToolResult>>(executionSettings?.ExtensionData, "tool_results", null);
        var rawPrompting = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "raw_prompting", (bool?)DefaultRawPrompting);

        var requestBody = new CommandRTextRequest.CommandRTextGenerationRequest
        {
            Message = prompt,
            Temperature = temperature,
            TopP = topP,
            TopK = topK,
            MaxTokens = maxTokens,
            StopSequences = stopSequences,
            PromptTruncation = promptTruncation,
            FrequencyPenalty = frequencyPenalty,
            PresencePenalty = presencePenalty,
            Seed = seed,
            ReturnPrompt = returnPrompt,
            Tools = tools,
            ToolResults = toolResults,
            RawPrompting = rawPrompting
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
                var responseBody = JsonSerializer.Deserialize<CommandRTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (!string.IsNullOrEmpty(responseBody?.Text))
                {
                    textContents.Add(new TextContent(responseBody.Text));
                }

                return textContents;
            }
        }
    }
    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by Cohere Command R.
    /// </summary>
    /// <param name="modelId">The model ID</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = chatHistory.Select(m => new Message
            {
                Role = this._util.MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", DefaultTemperature),
                TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "p", DefaultTopP),
                MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens)
            },
            AdditionalModelRequestFields = new Document
            {
                { "k", this._util.GetExtensionDataValue(settings?.ExtensionData, "k", DefaultTopK) },
                { "prompt_truncation", this._util.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation) },
                { "frequency_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
                { "presence_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) },
                { "seed", this._util.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed) },
                { "return_prompt", this._util.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt) },
                { "stop_sequences", new Document(this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null)?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
                { "raw_prompting", this._util.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", DefaultRawPrompting) }
            },
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };

        return converseRequest;
    }
    /// <summary>
    /// Extracts the text generation streaming output from the Cohere Command R response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["text"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }
    /// <summary>
    /// Builds the ConverseStreamRequest object for the Converse Bedrock API call, including building the Cohere Command R Request object and mapping parameters to the ConverseStreamRequest object.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = chatHistory.Select(m => new Message
        {
            Role = new BedrockUtilities().MapRole(m.Role),
            Content = new List<ContentBlock> { new() { Text = m.Content } }
        }).ToList();

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "p", DefaultTopP),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens)
        };

        var additionalModelRequestFields = new Document
        {
            { "k", this._util.GetExtensionDataValue(settings?.ExtensionData, "k", DefaultTopK) },
            { "prompt_truncation", this._util.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation) },
            { "frequency_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
            { "presence_penalty", this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) },
            { "seed", this._util.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed) },
            { "return_prompt", this._util.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt) },
            { "stop_sequences", new Document(this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null)?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
            { "raw_prompting", this._util.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", false) }
        };

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };

        return converseRequest;
    }
}
