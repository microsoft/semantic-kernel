// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Amazon.Bedrock.Core;

namespace Connectors.Amazon.Core;

/// <summary>
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
internal sealed class AI21JambaIOService : IBedrockModelIOService
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by AI21 Labs Jamba model.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        List<AI21JambaRequest.AI21TextGenerationRequest.Msg> messages = new()
        {
            new AI21JambaRequest.AI21TextGenerationRequest.Msg()
            {
                Role = "user",
                Content = prompt
            }
        };
        var requestBody = new AI21JambaRequest.AI21TextGenerationRequest()
        {
            Messages = messages,
            Temperature = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "temperature"),
            TopP = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "top_p"),
            MaxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "max_tokens"),
            Stop = BedrockModelUtilities.GetExtensionDataValue<IList<string>?>(executionSettings?.ExtensionData, "stop"),
            NumberOfResponses = BedrockModelUtilities.GetExtensionDataValue<int?>(executionSettings?.ExtensionData, "n"),
            FrequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "frequency_penalty"),
            PresencePenalty = BedrockModelUtilities.GetExtensionDataValue<double?>(executionSettings?.ExtensionData, "presence_penalty")
        };

        return requestBody;
    }

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns></returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());
        var textContents = new List<TextContent>();
        if (responseBody?.Choices is not { Count: > 0 })
        {
            return textContents;
        }
        textContents.AddRange(responseBody.Choices.Select(choice => new TextContent(choice.Message?.Content)));
        return textContents;
    }

    /// <summary>
    /// Builds the ConverseRequest object for the Bedrock ConverseAsync call with request parameters required by AI21 Labs Jamba.
    /// </summary>
    /// <param name="modelId">The model ID.</param>
    /// <param name="chatHistory">The messages between assistant and user.</param>
    /// <param name="settings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature");
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p");
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens");
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences");
        var n = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n");
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty");
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty");

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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
    /// <summary>
    /// Gets the streamed text output.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var buffer = new StringBuilder();
        if (chunk["choices"]?[0]?["delta"]?["content"] != null)
        {
            buffer.Append(chunk["choices"]?[0]?["delta"]?["content"]);
            yield return buffer.ToString();
        }
    }
    /// <summary>
    /// Gets converse stream output.
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);

        var temp = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "temperature");
        var topP = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "top_p");
        var maxTokens = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "max_tokens");
        var stopSequences = BedrockModelUtilities.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences");
        var n = BedrockModelUtilities.GetExtensionDataValue<int?>(settings?.ExtensionData, "n");
        var frequencyPenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "frequency_penalty");
        var presencePenalty = BedrockModelUtilities.GetExtensionDataValue<float?>(settings?.ExtensionData, "presence_penalty");

        var inferenceConfig = new InferenceConfiguration();
        BedrockModelUtilities.SetPropertyIfNotNull(() => temp, value => inferenceConfig.Temperature = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => topP, value => inferenceConfig.TopP = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => maxTokens, value => inferenceConfig.MaxTokens = value);
        BedrockModelUtilities.SetPropertyIfNotNull(() => stopSequences, value => inferenceConfig.StopSequences = value);

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
