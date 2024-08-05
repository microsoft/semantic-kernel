// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Cohere Command R.
/// </summary>
// ReSharper disable InconsistentNaming
internal sealed class CohereCommandRIOService : IBedrockModelIOService
// ReSharper restore InconsistentNaming
{
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
    private const bool DefaultSearchQueriesOnly = false;

    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command R.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var defaultChatHistory = new List<Dictionary<string, string>>
        {
            new()
            {
                { "role", "USER" },
                { "message", prompt }
            }
        };
        var requestBody = new
        {
            message = prompt,
            chat_history = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "chat_history", defaultChatHistory),
            documents = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "documents", new List<Document>()),
            search_queries_only = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "search_queries_only", DefaultSearchQueriesOnly),
            preamble = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "preamble", ""),
            max_tokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", DefaultTemperature),
            p = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "p", DefaultTopP),
            k = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "k", DefaultTopK),
            prompt_truncation = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation),
            frequency_penalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty),
            presence_penalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "presence_penalty", DefaultPresencePenalty),
            seed = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "seed", DefaultSeed),
            return_prompt = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "return_prompt", DefaultReturnPrompt),
            stop_sequences = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "stop_sequences", new List<string>()),
            raw_prompting = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "raw_prompting", DefaultRawPrompting)
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
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<CommandRTextResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (!string.IsNullOrEmpty(responseBody?.Text))
        {
            textContents.Add(new TextContent(responseBody.Text));
        }
        return textContents;
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
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", DefaultTemperature),
                TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "p", DefaultTopP),
                MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens)
            },
            AdditionalModelRequestFields = new Document
            {
                { "k", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "k", DefaultTopK) },
                { "prompt_truncation", BedrockModelUtilities.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation) },
                { "frequency_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
                { "presence_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) },
                { "seed", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed) },
                { "return_prompt", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt) },
                { "stop_sequences", new Document(BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []).Select(s => new Document(s)).ToList()) },
                { "raw_prompting", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", DefaultRawPrompting) }
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
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var inferenceConfig = new InferenceConfiguration
        {
            Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", DefaultTemperature),
            TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "p", DefaultTopP),
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens)
        };

        var additionalModelRequestFields = new Document
        {
            { "k", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "k", DefaultTopK) },
            { "prompt_truncation", BedrockModelUtilities.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation) },
            { "frequency_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty) },
            { "presence_penalty", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty) },
            { "seed", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed) },
            { "return_prompt", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt) },
            { "stop_sequences", new Document(BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []).Select(s => new Document(s)).ToList()) },
            { "raw_prompting", BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", false) }
        };

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };

        return converseRequest;
    }
}
