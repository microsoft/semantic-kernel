// Copyright (c) Microsoft. All rights reserved.

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
internal sealed class CohereCommandRIOService : IBedrockModelIOService
// ReSharper restore InconsistentNaming
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Cohere Command R.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    object IBedrockModelIOService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonCommandRExecutionSettings.FromExecutionSettings(executionSettings);
        var chatHistory = BedrockModelUtilities.GetExtensionDataValue<List<CommandRTools.ChatMessage>>(executionSettings?.ExtensionData, "chat_history") ?? exec.ChatHistory;
        if (chatHistory == null || chatHistory.Count == 0)
        {
            chatHistory = new List<CommandRTools.ChatMessage>
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
            Documents = BedrockModelUtilities.GetExtensionDataValue<List<CommandRTools.Document>?>(executionSettings?.ExtensionData, "documents") ?? exec.Documents,
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

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns></returns>
    IReadOnlyList<TextContent> IBedrockModelIOService.GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<CommandRResponse>(reader.ReadToEnd());
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
    ConverseRequest IBedrockModelIOService.GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
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
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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

    /// <summary>
    /// Extracts the text generation streaming output from the Cohere Command R response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    IEnumerable<string> IBedrockModelIOService.GetTextStreamOutput(JsonNode chunk)
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
    ConverseStreamRequest IBedrockModelIOService.GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
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
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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
