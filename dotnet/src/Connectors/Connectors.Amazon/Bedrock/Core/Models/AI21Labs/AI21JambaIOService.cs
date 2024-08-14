// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
internal sealed class AI21JambaIOService : IBedrockTextGenerationIOService, IBedrockChatCompletionIOService
{
    /// <inheritdoc/>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonJambaExecutionSettings.FromExecutionSettings(executionSettings);
        List<AI21JambaRequest.AI21TextGenerationRequest.JambaMessage> messages = new()
        {
            new AI21JambaRequest.AI21TextGenerationRequest.JambaMessage()
            {
                Role = "user",
                Content = prompt
            }
        };

        // Get the prompt execution settings from ExtensionData dictionary of PromptExecutionSettings or AmazonJambaTextExecutionSettings specific parameters.
        var requestBody = new AI21JambaRequest.AI21TextGenerationRequest()
        {
            Messages = messages,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(exec.ExtensionData, "temperature") ?? exec.Temperature,
            TopP = BedrockModelUtilities.GetExtensionDataValue<float?>(exec.ExtensionData, "top_p") ?? exec.TopP,
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(exec.ExtensionData, "max_tokens") ?? exec.MaxTokens,
            Stop = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(exec.ExtensionData, "stop") ?? exec.Stop,
            NumberOfResponses = BedrockModelUtilities.GetExtensionDataValue<int?>(exec.ExtensionData, "n") ?? exec.NumberOfResponses,
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(exec.ExtensionData, "frequency_penalty") ?? exec.FrequencyPenalty,
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(exec.ExtensionData, "presence_penalty") ?? exec.PresencePenalty
        };

        return requestBody;
    }

    /// <inheritdoc/>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var reader = new StreamReader(response.Body);
        var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());
        List<TextContent> textContents = [];
        if (responseBody?.Choices is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Choices.Select(choice => new TextContent(choice.Message?.Content)));
        return textContents;
    }

    /// <inheritdoc/>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonJambaExecutionSettings.FromExecutionSettings(settings);
        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? exec.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? exec.Stop;
        var n = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n") ?? exec.NumberOfResponses;
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty") ?? exec.FrequencyPenalty;
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty") ?? exec.PresencePenalty;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        if (n.HasValue)
        {
            additionalModelRequestFields.Add("n", n.Value);
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
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var buffer = new StringBuilder();
        if (chunk["choices"]?[0]?["delta"]?["content"] != null)
        {
            buffer.Append(chunk["choices"]?[0]?["delta"]?["content"]);
            yield return buffer.ToString();
        }
    }

    /// <inheritdoc/>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonJambaExecutionSettings.FromExecutionSettings(settings);
        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? exec.MaxTokens;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences") ?? exec.Stop;
        var n = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n") ?? exec.NumberOfResponses;
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty") ?? exec.FrequencyPenalty;
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty") ?? exec.PresencePenalty;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

        var additionalModelRequestFields = new Document();
        if (n.HasValue)
        {
            additionalModelRequestFields.Add("n", n.Value);
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
