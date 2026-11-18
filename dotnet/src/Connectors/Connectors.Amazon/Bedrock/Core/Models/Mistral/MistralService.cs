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
/// Input-output service for Mistral.
/// </summary>
internal sealed class MistralService : IBedrockTextGenerationService, IBedrockChatCompletionService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var settings = AmazonMistralExecutionSettings.FromExecutionSettings(executionSettings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? settings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "top_p") ?? settings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens") ?? settings.MaxTokens;
        var stop = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(executionSettings?.ExtensionData, "stop") ?? settings.StopSequences;
        var topK = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "top_k") ?? settings.TopK;

        var requestBody = new MistralRequest.MistralTextGenerationRequest()
        {
            Prompt = prompt,
            MaxTokens = maxTokens,
            StopSequences = stop,
            Temperature = temperature,
            TopP = topP,
            TopK = topK
        };

        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<MistralResponse>(reader.ReadToEnd());
        if (responseBody?.Outputs is not { Count: > 0 })
        {
            return [];
        }

        return responseBody.Outputs
                    .Select(output => new TextContent(output.Text, innerContent: responseBody))
                    .ToList();
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var executionSettings = AmazonMistralExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? executionSettings.TopK;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = []
        };
        return converseRequest;
    }

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        var outputs = chunk["outputs"]?.AsArray();
        if (outputs != null)
        {
            foreach (var output in outputs)
            {
                var text = output?["text"]?.ToString();
                if (!string.IsNullOrEmpty(text))
                {
                    yield return new StreamingTextContent(text, innerContent: chunk)!;
                }
            }
        }
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var executionSettings = AmazonMistralExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? executionSettings.TopK;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);

        var converseRequest = new ConverseStreamRequest()
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = []
        };
        return converseRequest;
    }
}
