// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Cohere Command R.
/// </summary>
// ReSharper disable InconsistentNaming
internal sealed class CohereCommandRService : IBedrockTextGenerationService, IBedrockChatCompletionService
// ReSharper restore InconsistentNaming
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonCommandRExecutionSettings.FromExecutionSettings(executionSettings);
        var chatHistory = BedrockModelUtilities.GetExtensionDataValue<List<CohereCommandRTools.ChatMessage>>(executionSettings?.ExtensionData, "chat_history") ?? exec.ChatHistory;
        if (chatHistory == null || chatHistory.Count == 0)
        {
            chatHistory = new List<CohereCommandRTools.ChatMessage>
            {
                new()
                {
                    Role = "USER",
                    Message = prompt
                }
            };
        }
        var requestBody = new CommandRRequest.CommandRTextGenerationRequest()
        {
            Message = prompt,
            ChatHistory = chatHistory,
            Documents = BedrockModelUtilities.GetExtensionDataValue<List<CohereCommandRTools.Document>?>(executionSettings?.ExtensionData, "documents") ?? exec.Documents,
            SearchQueriesOnly = BedrockModelUtilities.GetExtensionDataValue<bool?>(executionSettings?.ExtensionData, "search_queries_only") ?? exec.SearchQueriesOnly,
            Preamble = BedrockModelUtilities.GetExtensionDataValue<string?>(executionSettings?.ExtensionData, "preamble") ?? exec.Preamble,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens") ?? exec.MaxTokens,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? exec.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "p") ?? exec.TopP,
            TopK = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "k") ?? exec.TopK,
            PromptTruncation = BedrockModelUtilities.GetExtensionDataValue<string?>(executionSettings?.ExtensionData, "prompt_truncation") ?? exec.PromptTruncation,
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "frequency_penalty") ?? exec.FrequencyPenalty,
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "presence_penalty") ?? exec.PresencePenalty,
            Seed = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "seed") ?? exec.Seed,
            ReturnPrompt = BedrockModelUtilities.GetExtensionDataValue<bool?>(executionSettings?.ExtensionData, "return_prompt") ?? exec.ReturnPrompt,
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(executionSettings?.ExtensionData, "stop_sequences") ?? exec.StopSequences,
            RawPrompting = BedrockModelUtilities.GetExtensionDataValue<bool?>(executionSettings?.ExtensionData, "raw_prompting") ?? exec.RawPrompting
        };

        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<CommandRResponse>(reader.ReadToEnd());
        List<TextContent> textContents = [];
        if (!string.IsNullOrEmpty(responseBody?.Text))
        {
            textContents.Add(new TextContent(responseBody!.Text, innerContent: responseBody));
        }

        return textContents;
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonCommandRExecutionSettings.FromExecutionSettings(settings);
        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? exec.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? exec.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        var k = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "k") ?? exec.TopK;
        if (k.HasValue)
        {
            additionalModelRequestFields.Add("k", k.Value);
        }
        var promptTruncation = BedrockModelUtilities.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation") ?? exec.PromptTruncation;
        if (!string.IsNullOrEmpty(promptTruncation))
        {
            additionalModelRequestFields.Add("prompt_truncation", promptTruncation);
        }
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings?.ExtensionData, "frequency_penalty") ?? exec.FrequencyPenalty;
        if (frequencyPenalty.HasValue)
        {
            additionalModelRequestFields.Add("frequency_penalty", frequencyPenalty.Value);
        }
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings?.ExtensionData, "presence_penalty") ?? exec.PresencePenalty;
        if (presencePenalty.HasValue)
        {
            additionalModelRequestFields.Add("presence_penalty", presencePenalty.Value);
        }
        var seed = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "seed") ?? exec.Seed;
        if (seed.HasValue)
        {
            additionalModelRequestFields.Add("seed", seed.Value);
        }
        var returnPrompt = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "return_prompt") ?? exec.ReturnPrompt;
        if (returnPrompt.HasValue)
        {
            additionalModelRequestFields.Add("return_prompt", returnPrompt.Value);
        }
        var rawPrompting = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "raw_prompting") ?? exec.RawPrompting;
        if (rawPrompting.HasValue)
        {
            additionalModelRequestFields.Add("raw_prompting", rawPrompting.Value);
        }
        var converseRequest = new ConverseRequest
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

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["text"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return new StreamingTextContent(text, innerContent: chunk)!;
        }
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var executionSettings = AmazonCommandRExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? executionSettings.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? executionSettings.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        var k = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "k") ?? executionSettings.TopK;
        if (k.HasValue)
        {
            additionalModelRequestFields.Add("k", k.Value);
        }
        var promptTruncation = BedrockModelUtilities.GetExtensionDataValue<string>(settings?.ExtensionData, "prompt_truncation") ?? executionSettings.PromptTruncation;
        if (!string.IsNullOrEmpty(promptTruncation))
        {
            additionalModelRequestFields.Add("prompt_truncation", promptTruncation);
        }
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings?.ExtensionData, "frequency_penalty") ?? executionSettings.FrequencyPenalty;
        if (frequencyPenalty.HasValue)
        {
            additionalModelRequestFields.Add("frequency_penalty", frequencyPenalty.Value);
        }
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings?.ExtensionData, "presence_penalty") ?? executionSettings.PresencePenalty;
        if (presencePenalty.HasValue)
        {
            additionalModelRequestFields.Add("presence_penalty", presencePenalty.Value);
        }
        var seed = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "seed") ?? executionSettings.Seed;
        if (seed.HasValue)
        {
            additionalModelRequestFields.Add("seed", seed.Value);
        }
        var returnPrompt = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "return_prompt") ?? executionSettings.ReturnPrompt;
        if (returnPrompt.HasValue)
        {
            additionalModelRequestFields.Add("return_prompt", returnPrompt.Value);
        }
        var rawPrompting = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "raw_prompting") ?? executionSettings.RawPrompting;
        if (rawPrompting.HasValue)
        {
            additionalModelRequestFields.Add("raw_prompting", rawPrompting.Value);
        }
        var converseRequest = new ConverseStreamRequest()
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
