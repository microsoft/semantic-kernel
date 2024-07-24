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
    private const double DefaultTemperature = 0.3;
    private const double DefaultTopP = 0.75;
    private const double DefaultTopK = 0.0;
    private const string DefaultPromptTruncation = "OFF";
    private const double DefaultFrequencyPenalty = 0.0;
    private const double DefaultPresencePenalty = 0.0;
    private const int DefaultSeed = 0;
    private const bool DefaultReturnPrompt = false;
    private const bool DefaultRawPrompting = false;
    private const int DefaultMaxTokens = 128000;
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command R.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        double? temperature = DefaultTemperature;
        double? topP = DefaultTopP;
        int? maxTokens = DefaultMaxTokens;
        List<string>? stopSequences = null;
        double? topK = DefaultTopK;
        string? promptTruncation = DefaultPromptTruncation;
        double? frequencyPenalty = DefaultFrequencyPenalty;
        double? presencePenalty = DefaultPresencePenalty;
        int? seed = DefaultSeed;
        bool? returnPrompt = DefaultReturnPrompt;
        List<CommandRTextRequest.Tool>? tools = null;
        List<CommandRTextRequest.ToolResult>? toolResults = null;
        bool? rawPrompting = DefaultRawPrompting;

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

            executionSettings.ExtensionData.TryGetValue("prompt_truncation", out var promptTruncationValue);
            promptTruncation = promptTruncationValue as string;

            executionSettings.ExtensionData.TryGetValue("frequency_penalty", out var frequencyPenaltyValue);
            frequencyPenalty = frequencyPenaltyValue as double?;

            executionSettings.ExtensionData.TryGetValue("presence_penalty", out var presencePenaltyValue);
            presencePenalty = presencePenaltyValue as double?;

            executionSettings.ExtensionData.TryGetValue("seed", out var seedValue);
            seed = seedValue as int?;

            executionSettings.ExtensionData.TryGetValue("return_prompt", out var returnPromptValue);
            returnPrompt = returnPromptValue as bool?;

            executionSettings.ExtensionData.TryGetValue("tools", out var toolsValue);
            tools = toolsValue as List<CommandRTextRequest.Tool>;

            executionSettings.ExtensionData.TryGetValue("tool_results", out var toolResultsValue);
            toolResults = toolResultsValue as List<CommandRTextRequest.ToolResult>;

            executionSettings.ExtensionData.TryGetValue("raw_prompting", out var rawPromptingValue);
            rawPrompting = rawPromptingValue as bool?;
        }

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
        var cohereRequest = new CohereCommandRequest
        {
            ChatHistory = chatHistory.Select(m => new CohereCommandRequest.CohereMessage
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Message = m.Content
            }).ToList(),
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "p", (float)DefaultTopP),
            TopK = this._util.GetExtensionDataValue(settings?.ExtensionData, "k", (float)DefaultTopK),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            PromptTruncation = this._util.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation),
            FrequencyPenalty = this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty),
            PresencePenalty = this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty),
            Seed = this._util.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed),
            ReturnPrompt = this._util.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt),
            Tools = this._util.GetExtensionDataValue<List<CohereCommandRequest.CohereTool>>(settings?.ExtensionData, "tools", null),
            ToolResults = this._util.GetExtensionDataValue<List<CohereCommandRequest.CohereToolResult>>(settings?.ExtensionData, "tool_results", null),
            StopSequences = this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null),
            RawPrompting = this._util.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", false)
        };
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = cohereRequest.Messages,
            System = cohereRequest.System,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = cohereRequest.Temperature,
                TopP = cohereRequest.TopP,
                MaxTokens = cohereRequest.MaxTokens
            },
            AdditionalModelRequestFields = new Document
            {
                { "message", cohereRequest.Message },
                { "documents", new Document(cohereRequest.Documents?.Select(d => new Document
                {
                    { "title", d.Title },
                    { "snippet", d.Snippet }
                }).ToList() ?? new List<Document>()) },
                { "search_queries_only", cohereRequest.SearchQueriesOnly },
                { "preamble", cohereRequest.Preamble },
                { "k", cohereRequest.TopK },
                { "prompt_truncation", cohereRequest.PromptTruncation },
                { "frequency_penalty", cohereRequest.FrequencyPenalty },
                { "presence_penalty", cohereRequest.PresencePenalty },
                { "seed", cohereRequest.Seed },
                { "return_prompt", cohereRequest.ReturnPrompt },
                { "stop_sequences", new Document(cohereRequest.StopSequences?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
                { "raw_prompting", cohereRequest.RawPrompting }
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
        var cohereRequest = new CohereCommandRequest
        {
            ChatHistory = chatHistory.Select(m => new CohereCommandRequest.CohereMessage
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Message = m.Content
            }).ToList(),
            Messages = chatHistory.Select(m => new Message
            {
                Role = new BedrockUtilities().MapRole(m.Role),
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            Temperature = this._util.GetExtensionDataValue(settings?.ExtensionData, "temperature", (float)DefaultTemperature),
            TopP = this._util.GetExtensionDataValue(settings?.ExtensionData, "p", (float)DefaultTopP),
            TopK = this._util.GetExtensionDataValue(settings?.ExtensionData, "k", (float)DefaultTopK),
            MaxTokens = this._util.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", DefaultMaxTokens),
            PromptTruncation = this._util.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation", DefaultPromptTruncation),
            FrequencyPenalty = this._util.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", DefaultFrequencyPenalty),
            PresencePenalty = this._util.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", DefaultPresencePenalty),
            Seed = this._util.GetExtensionDataValue(settings?.ExtensionData, "seed", DefaultSeed),
            ReturnPrompt = this._util.GetExtensionDataValue(settings?.ExtensionData, "return_prompt", DefaultReturnPrompt),
            Tools = this._util.GetExtensionDataValue<List<CohereCommandRequest.CohereTool>>(settings?.ExtensionData, "tools", null),
            ToolResults = this._util.GetExtensionDataValue<List<CohereCommandRequest.CohereToolResult>>(settings?.ExtensionData, "tool_results", null),
            StopSequences = this._util.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null),
            RawPrompting = this._util.GetExtensionDataValue(settings?.ExtensionData, "raw_prompting", false)
        };
        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = cohereRequest.Messages,
            System = cohereRequest.System,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = (float)cohereRequest.Temperature,
                TopP = (float)cohereRequest.TopP,
                MaxTokens = cohereRequest.MaxTokens
            },
            AdditionalModelRequestFields = new Document
            {
                { "message", cohereRequest.Message },
                {
                    "documents", new Document(cohereRequest.Documents?.Select(d => new Document
                    {
                        { "title", d.Title },
                        { "snippet", d.Snippet }
                    }).ToList() ?? new List<Document>())
                },
                { "search_queries_only", cohereRequest.SearchQueriesOnly },
                { "preamble", cohereRequest.Preamble },
                { "k", cohereRequest.TopK },
                { "prompt_truncation", cohereRequest.PromptTruncation },
                { "frequency_penalty", cohereRequest.FrequencyPenalty },
                { "presence_penalty", cohereRequest.PresencePenalty },
                { "seed", cohereRequest.Seed },
                { "return_prompt", cohereRequest.ReturnPrompt },
                { "stop_sequences", new Document(cohereRequest.StopSequences?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
                { "raw_prompting", cohereRequest.RawPrompting }
            },
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
        };
        return converseRequest;
    }
}
