// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Anthropic Claude model.
/// </summary>
internal sealed class AnthropicService : IBedrockTextGenerationService, IBedrockChatCompletionService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var settings = AmazonClaudeExecutionSettings.FromExecutionSettings(executionSettings);
        var requestBody = new ClaudeRequest.ClaudeTextGenerationRequest()
        {
            Prompt = prompt,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "temperature") ?? settings.Temperature,
            MaxTokensToSample = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens_to_sample") ?? settings.MaxTokensToSample,
            StopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stop_sequences") ?? settings.StopSequences,
            TopP = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "top_p") ?? settings.TopP,
            TopK = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "top_k") ?? settings.TopK
        };
        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<ClaudeResponse>(reader.ReadToEnd());
        List<TextContent> textContents = [];
        if (!string.IsNullOrEmpty(responseBody?.Completion))
        {
            textContents.Add(new TextContent(responseBody!.Completion, innerContent: responseBody));
        }

        return textContents;
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var executionSettings = AmazonClaudeExecutionSettings.FromExecutionSettings(settings);
        
        // Get cache settings from execution settings
        var enableSystemCaching = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "enable_system_caching") ?? executionSettings.EnableSystemCaching;
        var enableMessageCaching = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "enable_message_caching") ?? executionSettings.EnableMessageCaching;
        var systemCacheBreakpoint = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "system_cache_breakpoint") ?? executionSettings.SystemCacheBreakpoint;
        var messageCacheBreakpoints = BedrockModelUtilities.GetExtensionDataValue<List<int>?>(settings?.ExtensionData, "message_cache_breakpoints") ?? executionSettings.MessageCacheBreakpoints;

        // Build messages and system messages with optional caching
        var messages = enableMessageCaching 
            ? BedrockModelUtilities.BuildMessageListWithCaching(chatHistory, enableMessageCaching, messageCacheBreakpoints)
            : BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = enableSystemCaching 
            ? BedrockModelUtilities.GetSystemMessagesWithCaching(chatHistory, enableSystemCaching, systemCacheBreakpoint)
            : BedrockModelUtilities.GetSystemMessages(chatHistory);

        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens_to_sample") ?? executionSettings.MaxTokensToSample;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? executionSettings.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        inferenceConfig.MaxTokens = maxTokens; // Max Token Count required (cannot be null).
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        List<ClaudeToolUse.ClaudeTool>? tools = null;
        ClaudeToolUse.ClaudeToolChoice? toolChoice = null;

        if (modelId != "anthropic.claude-instant-v1" && settings?.ExtensionData != null)
        {
            if (settings.ExtensionData.ContainsKey("tools"))
            {
                tools = BedrockModelUtilities.GetExtensionDataValue<List<ClaudeToolUse.ClaudeTool>?>(settings.ExtensionData, "tools");
            }

            if (settings.ExtensionData.ContainsKey("tool_choice"))
            {
                toolChoice = BedrockModelUtilities.GetExtensionDataValue<ClaudeToolUse.ClaudeToolChoice?>(settings.ExtensionData, "tool_choice");
            }
        }

        if (tools != null)
        {
            additionalModelRequestFields.Add(
                "tools", new Document(tools.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList())
            );
        }

        if (toolChoice != null)
        {
            additionalModelRequestFields.Add(
                "tool_choice", new Document
                {
                    { "type", toolChoice.Type },
                    { "name", toolChoice.Name }
                }
            );
        }

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };

        return converseRequest;
    }

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["completion"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return new StreamingTextContent(text, innerContent: chunk)!;
        }
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var executionSettings = AmazonClaudeExecutionSettings.FromExecutionSettings(settings);
        
        // Get cache settings from execution settings
        var enableSystemCaching = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "enable_system_caching") ?? executionSettings.EnableSystemCaching;
        var enableMessageCaching = BedrockModelUtilities.GetExtensionDataValue<bool?>(settings?.ExtensionData, "enable_message_caching") ?? executionSettings.EnableMessageCaching;
        var systemCacheBreakpoint = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "system_cache_breakpoint") ?? executionSettings.SystemCacheBreakpoint;
        var messageCacheBreakpoints = BedrockModelUtilities.GetExtensionDataValue<List<int>?>(settings?.ExtensionData, "message_cache_breakpoints") ?? executionSettings.MessageCacheBreakpoints;

        // Build messages and system messages with optional caching
        var messages = enableMessageCaching 
            ? BedrockModelUtilities.BuildMessageListWithCaching(chatHistory, enableMessageCaching, messageCacheBreakpoints)
            : BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = enableSystemCaching 
            ? BedrockModelUtilities.GetSystemMessagesWithCaching(chatHistory, enableSystemCaching, systemCacheBreakpoint)
            : BedrockModelUtilities.GetSystemMessages(chatHistory);

        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens_to_sample") ?? executionSettings.MaxTokensToSample;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? executionSettings.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        inferenceConfig.MaxTokens = maxTokens; // Max Token Count required (cannot be null).
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        List<ClaudeToolUse.ClaudeTool>? tools = null;
        ClaudeToolUse.ClaudeToolChoice? toolChoice = null;

        if (modelId != "anthropic.claude-instant-v1" && settings?.ExtensionData != null)
        {
            if (settings.ExtensionData.ContainsKey("tools"))
            {
                tools = BedrockModelUtilities.GetExtensionDataValue<List<ClaudeToolUse.ClaudeTool>?>(settings.ExtensionData, "tools");
            }

            if (settings.ExtensionData.ContainsKey("tool_choice"))
            {
                toolChoice = BedrockModelUtilities.GetExtensionDataValue<ClaudeToolUse.ClaudeToolChoice?>(settings.ExtensionData, "tool_choice");
            }
        }

        if (tools != null)
        {
            additionalModelRequestFields.Add(
                "tools", new Document(tools.Select(t => new Document
                {
                    { "name", t.Name },
                    { "description", t.Description },
                    { "input_schema", t.InputSchema }
                }).ToList())
            );
        }

        if (toolChoice != null)
        {
            additionalModelRequestFields.Add(
                "tool_choice", new Document
                {
                    { "type", toolChoice.Type },
                    { "name", toolChoice.Name }
                }
            );
        }

        var converseRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };

        return converseRequest;
    }
}
