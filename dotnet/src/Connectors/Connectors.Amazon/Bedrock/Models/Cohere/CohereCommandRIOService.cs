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
        var temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", (double?)DefaultTemperature);
        var topP = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "p", (double?)DefaultTopP);
        var topK = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "k", (double?)DefaultTopK);
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", (int?)DefaultMaxTokens);
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stop_sequences", null);
        var promptTruncation = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation);
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "frequency_penalty", (double?)DefaultFrequencyPenalty);
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "presence_penalty", (double?)DefaultPresencePenalty);
        var seed = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "seed", (int?)DefaultSeed);
        var returnPrompt = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "return_prompt", (bool?)DefaultReturnPrompt);
        var tools = BedrockModelUtilities.GetExtensionDataValue<List<CommandRTextRequest.Tool>>(executionSettings?.ExtensionData, "tools", null);
        var toolResults = BedrockModelUtilities.GetExtensionDataValue<List<CommandRTextRequest.ToolResult>>(executionSettings?.ExtensionData, "tool_results", null);
        var rawPrompting = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "raw_prompting", (bool?)DefaultRawPrompting);

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
                { "stop_sequences", new Document(BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null)?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
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
            { "stop_sequences", new Document(BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null)?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
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
