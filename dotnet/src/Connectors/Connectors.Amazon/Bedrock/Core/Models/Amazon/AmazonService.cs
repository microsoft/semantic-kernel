// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Nova;
using Microsoft.SemanticKernel.Connectors.Nova.Core;
using static Microsoft.SemanticKernel.Connectors.Nova.Core.NovaRequest;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Amazon Titan model.
/// </summary>
internal sealed class AmazonService : IBedrockTextGenerationService, IBedrockChatCompletionService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        if (modelId.StartsWith("amazon.titan-", StringComparison.OrdinalIgnoreCase))
        {
            var settings = AmazonTitanExecutionSettings.FromExecutionSettings(executionSettings);
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? settings.Temperature;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "topP") ?? settings.TopP;
            var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "maxTokenCount") ?? settings.MaxTokenCount;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stopSequences") ?? settings.StopSequences;

            var requestBody = new TitanRequest.TitanTextGenerationRequest()
            {
                InputText = prompt,
                TextGenerationConfig = new TitanRequest.AmazonTitanTextGenerationConfig()
                {
                    MaxTokenCount = maxTokenCount,
                    TopP = topP,
                    Temperature = temperature,
                    StopSequences = stopSequences
                }
            };
            return requestBody;
        }

        if (modelId.StartsWith("amazon.nova-", StringComparison.OrdinalIgnoreCase))
        {
            var settings = AmazonNovaExecutionSettings.FromExecutionSettings(executionSettings);
            var schemaVersion = BedrockModelUtilities.GetExtensionDataValue<string?>(executionSettings?.ExtensionData, "schemaVersion") ?? settings.SchemaVersion;
            var maxNewTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_new_tokens") ?? settings.MaxNewTokens;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "top_p") ?? settings.TopP;
            var topK = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "top_k") ?? settings.TopK;
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? settings.Temperature;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stopSequences") ?? settings.StopSequences;

            var requestBody = new NovaRequest.NovaTextGenerationRequest()
            {
                InferenceConfig = new NovaRequest.NovaTextGenerationConfig
                {
                    MaxNewTokens = maxNewTokens,
                    Temperature = temperature,
                    TopK = topK,
                    TopP = topP
                },
                Messages = new List<NovaRequest.NovaUserMessage> { new() { Role = AuthorRole.User.Label, Content = new List<NovaUserMessageContent> { new() { Text = prompt } } } },
                SchemaVersion = schemaVersion ?? "messages-v1",
            };
            return requestBody;
        }

        throw new NotSupportedException($"Amazon model '{modelId}' is not supported. Supported models: Titan and Nova.");
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(string modelId, InvokeModelResponse response)
    {
        if (modelId.StartsWith("amazon.titan-", StringComparison.OrdinalIgnoreCase))
        {
            using var reader = new StreamReader(response.Body);
            var responseBody = JsonSerializer.Deserialize<TitanTextResponse>(reader.ReadToEnd());
            List<TextContent> textContents = [];
            if (responseBody?.Results is not { Count: > 0 })
            {
                return textContents;
            }
            string? outputText = responseBody.Results[0].OutputText;
            textContents.Add(new TextContent(outputText));
            return textContents;
        }

        if (modelId.StartsWith("amazon.nova-", StringComparison.OrdinalIgnoreCase))
        {
            using var reader = new StreamReader(response.Body);
            var responseBody = JsonSerializer.Deserialize<NovaTextResponse>(reader.ReadToEnd(), new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
            List<TextContent> textContents = [];
            if (responseBody?.Output?.Message?.Contents is not { Count: > 0 })
            {
                return textContents;
            }
            string? outputText = responseBody.Output.Message.Contents[0].Text;
            textContents.Add(new TextContent(outputText));
            return textContents;
        }

        throw new NotSupportedException($"Amazon model '{modelId}' is not supported. Supported models: Titan and Nova.");
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        if (modelId.StartsWith("amazon.titan-", StringComparison.OrdinalIgnoreCase))
        {
            var executionSettings = AmazonTitanExecutionSettings.FromExecutionSettings(settings);
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "topP") ?? executionSettings.TopP;
            var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "maxTokenCount") ?? executionSettings.MaxTokenCount;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? executionSettings.StopSequences;

            var inferenceConfig = new InferenceConfiguration();
            BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokenCount, value => inferenceConfig.MaxTokens = value);
            BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

            var converseRequest = new ConverseRequest
            {
                ModelId = modelId,
                Messages = messages,
                System = systemMessages,
                InferenceConfig = inferenceConfig,
                AdditionalModelRequestFields = new Document(),
                AdditionalModelResponseFieldPaths = new List<string>()
            };

            return converseRequest;
        }

        if (modelId.StartsWith("amazon.nova-", StringComparison.OrdinalIgnoreCase))
        {
            var executionSettings = AmazonNovaExecutionSettings.FromExecutionSettings(settings);
            var schemaVersion = BedrockModelUtilities.GetExtensionDataValue<string?>(settings?.ExtensionData, "schemaVersion") ?? executionSettings.SchemaVersion;
            var maxNewTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_new_tokens") ?? executionSettings.MaxNewTokens;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
            var topK = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "top_k") ?? executionSettings.TopK;
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? executionSettings.StopSequences;

            var inferenceConfig = new InferenceConfiguration();
            BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => maxNewTokens, value => inferenceConfig.MaxTokens = value);
            BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

            var converseRequest = new ConverseRequest
            {
                ModelId = modelId,
                Messages = messages,
                System = systemMessages,
                InferenceConfig = inferenceConfig,
                AdditionalModelRequestFields = new Document(),
                AdditionalModelResponseFieldPaths = new List<string>()
            };

            return converseRequest;
        }

        throw new NotSupportedException($"Amazon model '{modelId}' is not supported. Supported models: Titan and Nova.");
    }

    /// <inheritdoc/>
    public IEnumerable<string> GetTextStreamOutput(string modelId, JsonNode chunk)
    {
        if (modelId.StartsWith("amazon.titan-", StringComparison.OrdinalIgnoreCase))
        {
            var text = chunk["outputText"]?.ToString();
            if (!string.IsNullOrEmpty(text))
            {
                yield return text!;
            }
        }

        if (modelId.StartsWith("amazon.nova-", StringComparison.OrdinalIgnoreCase))
        {
            var text = chunk["output"]?["message"]?["content"]?["text"]?.ToString();
            if (!string.IsNullOrEmpty(text))
            {
                yield return text!;
            }
        }
        throw new NotSupportedException($"Amazon model '{modelId}' is not supported. Supported models: Titan and Nova.");
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        if (modelId.StartsWith("amazon.titan-", StringComparison.OrdinalIgnoreCase))
        {
            var executionSettings = AmazonTitanExecutionSettings.FromExecutionSettings(settings);
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "topP") ?? executionSettings.TopP;
            var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "maxTokenCount") ?? executionSettings.MaxTokenCount;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? executionSettings.StopSequences;

            var inferenceConfig = new InferenceConfiguration();
            BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokenCount, value => inferenceConfig.MaxTokens = value);
            BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

            var converseRequest = new ConverseStreamRequest()
            {
                ModelId = modelId,
                Messages = messages,
                System = systemMessages,
                InferenceConfig = inferenceConfig,
                AdditionalModelRequestFields = new Document(),
                AdditionalModelResponseFieldPaths = new List<string>()
            };

            return converseRequest;
        }

        if (modelId.StartsWith("amazon.nova-", StringComparison.OrdinalIgnoreCase))
        {
            var executionSettings = AmazonNovaExecutionSettings.FromExecutionSettings(settings);
            var schemaVersion = BedrockModelUtilities.GetExtensionDataValue<string?>(settings?.ExtensionData, "schemaVersion") ?? executionSettings.SchemaVersion;
            var maxNewTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_new_tokens") ?? executionSettings.MaxNewTokens;
            var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
            var topK = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "top_k") ?? executionSettings.TopK;
            var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
            var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? executionSettings.StopSequences;

            var inferenceConfig = new InferenceConfiguration();
            BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
            BedrockModelUtilities.SetPropertyIfNotNull(() => maxNewTokens, value => inferenceConfig.MaxTokens = value);
            BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

            var converseRequest = new ConverseStreamRequest
            {
                ModelId = modelId,
                Messages = messages,
                System = systemMessages,
                InferenceConfig = inferenceConfig,
                AdditionalModelRequestFields = new Document(),
                AdditionalModelResponseFieldPaths = new List<string>()
            };

            return converseRequest;
        }

        throw new NotSupportedException($"Amazon model '{modelId}' is not supported. Supported models: Titan and Nova.");
    }
}
