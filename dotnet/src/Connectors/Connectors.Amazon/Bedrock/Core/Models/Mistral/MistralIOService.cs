// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Mistral.
/// </summary>
internal sealed class MistralIOService : IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Mistral.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    object IBedrockModelIOService.GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings)
    {
        var exec = AmazonMistralExecutionSettings.FromExecutionSettings(executionSettings);
        var temperature = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(executionSettings?.ExtensionData, "top_p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens") ?? exec.MaxTokens;
        var stop = BedrockModelUtilities.GetExtensionDataValue<List<string>?>(executionSettings?.ExtensionData, "stop") ?? exec.StopSequences;
        var topK = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "top_k") ?? exec.TopK;

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

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns>A list of text content objects as required by the semantic kernel.</returns>
    IReadOnlyList<TextContent> IBedrockModelIOService.GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<MistralResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Outputs is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Outputs.Select(output => new TextContent(output.Text)));
        return textContents;
    }

    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by Mistral.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    ConverseRequest IBedrockModelIOService.GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonMistralExecutionSettings.FromExecutionSettings(settings);
        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? exec.TopK;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);

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
    /// Extracts the text generation streaming output from the Mistral response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    IEnumerable<string> IBedrockModelIOService.GetTextStreamOutput(JsonNode chunk)
    {
        var outputs = chunk["outputs"]?.AsArray();
        if (outputs != null)
        {
            foreach (var output in outputs)
            {
                var text = output?["text"]?.ToString();
                if (!string.IsNullOrEmpty(text))
                {
                    yield return text;
                }
            }
        }
    }

    /// <summary>
    /// Builds the ConverseStreamRequest object for the Converse Bedrock API call, including building the Mistral Request object and mapping parameters to the ConverseStreamRequest object.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    ConverseStreamRequest IBedrockModelIOService.GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var exec = AmazonMistralExecutionSettings.FromExecutionSettings(settings);
        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature") ?? exec.Temperature;
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p") ?? exec.TopP;
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens") ?? exec.TopK;

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);

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
