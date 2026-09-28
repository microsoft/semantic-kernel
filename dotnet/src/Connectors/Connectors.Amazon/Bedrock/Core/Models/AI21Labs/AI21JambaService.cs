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
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
internal sealed class AI21JambaService : IBedrockTextGenerationService, IBedrockChatCompletionService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var settings = AmazonJambaExecutionSettings.FromExecutionSettings(executionSettings);
        List<AI21JambaRequest.AI21TextGenerationRequest.JambaMessage> messages =
        [
            new AI21JambaRequest.AI21TextGenerationRequest.JambaMessage()
            {
                Role = "user",
                Content = prompt
            }
        ];

        // Get the prompt execution settings from ExtensionData dictionary of PromptExecutionSettings or AmazonJambaTextExecutionSettings specific parameters.
        var requestBody = new AI21JambaRequest.AI21TextGenerationRequest()
        {
            Messages = messages,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings.ExtensionData, "temperature") ?? settings.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings.ExtensionData, "top_p") ?? settings.TopP,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings.ExtensionData, "max_tokens") ?? settings.MaxTokens,
            Stop = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(settings.ExtensionData, "stop") ?? settings.Stop,
            NumberOfResponses = BedrockModelUtilities.GetExtensionDataValue<int?>(settings.ExtensionData, "n") ?? settings.NumberOfResponses,
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings.ExtensionData, "frequency_penalty") ?? settings.FrequencyPenalty,
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(settings.ExtensionData, "presence_penalty") ?? settings.PresencePenalty
        };

        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());

        if (responseBody?.Choices is not { Count: > 0 })
        {
            return [];
        }

        return responseBody.Choices
            .Select(choice => new TextContent(choice.Message?.Content, innerContent: responseBody))
            .ToList();
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var executionSettings = AmazonJambaExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? executionSettings.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? executionSettings.Stop;
        var numberOfResponses = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n") ?? executionSettings.NumberOfResponses;
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty") ?? executionSettings.FrequencyPenalty;
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty") ?? executionSettings.PresencePenalty;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        if (numberOfResponses.HasValue)
        {
            additionalModelRequestFields.Add("n", numberOfResponses.Value);
        }
        if (frequencyPenalty.HasValue)
        {
            additionalModelRequestFields.Add("frequency_penalty", frequencyPenalty.Value);
        }
        if (presencePenalty.HasValue)
        {
            additionalModelRequestFields.Add("presence_penalty", presencePenalty.Value);
        }

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = []
        };

        return converseRequest;
    }

    /// <inheritdoc/>
    public IEnumerable<StreamingTextContent> GetTextStreamOutput(JsonNode chunk)
    {
        var choiceDeltaContent = chunk["choices"]?[0]?["delta"]?["content"];
        if (choiceDeltaContent is not null)
        {
            yield return new StreamingTextContent(choiceDeltaContent.ToString(), innerContent: chunk);
        }
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var executionSettings = AmazonJambaExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? executionSettings.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? executionSettings.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? executionSettings.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? executionSettings.Stop;
        var numberOfResponses = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n") ?? executionSettings.NumberOfResponses;
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty") ?? executionSettings.FrequencyPenalty;
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty") ?? executionSettings.PresencePenalty;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetNullablePropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        if (numberOfResponses.HasValue)
        {
            additionalModelRequestFields.Add("n", numberOfResponses.Value);
        }
        if (frequencyPenalty.HasValue)
        {
            additionalModelRequestFields.Add("frequency_penalty", frequencyPenalty.Value);
        }
        if (presencePenalty.HasValue)
        {
            additionalModelRequestFields.Add("presence_penalty", presencePenalty.Value);
        }

        var converseRequest = new ConverseStreamRequest()
        {
            ModelId = modelId,
            Messages = messages,
            System = systemMessages,
            InferenceConfig = inferenceConfig,
            AdditionalModelRequestFields = additionalModelRequestFields,
            AdditionalModelResponseFieldPaths = []
        };

        return converseRequest;
    }
}
