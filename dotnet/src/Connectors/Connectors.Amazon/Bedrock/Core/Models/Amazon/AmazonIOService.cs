// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Amazon Titan model.
/// </summary>
internal sealed class AmazonIOService : IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Amazon Titan.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    object IBedrockModelIOService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonTitanExecutionSettings.FromExecutionSettings(executionSettings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "topP") ?? exec.TopP;
        var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "maxTokenCount") ?? exec.MaxTokenCount;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stopSequences") ?? exec.StopSequences;

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
        var responseBody = JsonSerializer.Deserialize<TitanTextResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Results is not { Count: > 0 })
        {
            return textContents;
        }
        string? outputText = responseBody.Results[0].OutputText;
        textContents.Add(new TextContent(outputText));
        return textContents;
    }

    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by Amazon Titan.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    ConverseRequest IBedrockModelIOService.GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonTitanExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "topP") ?? exec.TopP;
        var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "maxTokenCount") ?? exec.MaxTokenCount;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? exec.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokenCount, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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

    /// <summary>
    /// Extracts the text generation streaming output from the Amazon Titan response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    IEnumerable<string> IBedrockModelIOService.GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk["outputText"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }

    /// <summary>
    /// Builds the ConverseStreamRequest object for the Converse Bedrock API call, including building the Amazon Titan Request object and mapping parameters to the ConverseStreamRequest object.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    ConverseStreamRequest IBedrockModelIOService.GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonTitanExecutionSettings.FromExecutionSettings(settings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "topP") ?? exec.TopP;
        var maxTokenCount = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "maxTokenCount") ?? exec.MaxTokenCount;
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(settings?.ExtensionData, "stopSequences") ?? exec.StopSequences;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temperature, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokenCount, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetStopSequenceIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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
}
