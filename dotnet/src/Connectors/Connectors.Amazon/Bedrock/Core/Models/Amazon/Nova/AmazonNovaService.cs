// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Core;
using static Microsoft.SemanticKernel.Connectors.Amazon.Nova.NovaRequest;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Nova;

internal sealed class AmazonNovaService : IBedrockTextGenerationService, IBedrockChatCompletionService
{
    ConverseRequest IBedrockChatCompletionService.GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

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

    ConverseStreamRequest IBedrockChatCompletionService.GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        throw new System.NotImplementedException();
    }

    object IBedrockTextGenerationService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
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

    IReadOnlyList<TextContent> IBedrockTextGenerationService.GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<NovaTextResponse>(reader.ReadToEnd(), new JsonSerializerOptions { PropertyNameCaseInsensitive = true });
        List<TextContent> textContents = [];
        if (responseBody?.Output?.Message?.Contents is not { Count: > 0 })
        {
            return textContents;
        }
        string? outputText = responseBody.Output.Message.Contents[0].Text;
        return [new TextContent(outputText, innerContent: responseBody)];
    }

    IEnumerable<StreamingTextContent> IBedrockTextGenerationService.GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["output"]?["message"]?["content"]?["text"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return new StreamingTextContent(text, innerContent: chunk)!;
        }
    }
}
