// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Core;

/// <summary>
/// Input-output service for Mistral.
/// </summary>
internal sealed class MistralIOService : IBedrockModelIOService
{
    // Define constants for default values
    private const float DefaultTemperatureInstruct = 0.5f;
    private const float DefaultTopPInstruct = 0.9f;
    private const int DefaultMaxTokensInstruct = 512;
    private const int DefaultTopKInstruct = 50;
    private static readonly List<string> s_defaultStopSequencesInstruct = new();

    private const float DefaultTemperatureNonInstruct = 0.7f;
    private const float DefaultTopPNonInstruct = 1.0f;
    private const int DefaultMaxTokensNonInstruct = 8192;
    private const int DefaultTopKNonInstruct = 0;
    private static readonly List<string> s_defaultStopSequencesNonInstruct = new();

    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Mistral.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        // var isInstructModel = modelId.Contains("instruct", StringComparison.OrdinalIgnoreCase);
        // var temperature = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", isInstructModel ? DefaultTemperatureInstruct : (double?)DefaultTemperatureNonInstruct);
        // var topP = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", isInstructModel ? DefaultTopPInstruct : (double?)DefaultTopPNonInstruct);
        // var maxTokens = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", isInstructModel ? DefaultMaxTokensInstruct : (int?)DefaultMaxTokensNonInstruct);
        // var stop = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "stop", isInstructModel ? s_defaultStopSequencesInstruct : s_defaultStopSequencesNonInstruct);
        // var topK = BedrockModelUtilities.GetExtensionDataValue(executionSettings?.ExtensionData, "top_k", isInstructModel ? DefaultTopKInstruct : (int?)DefaultTopKNonInstruct);
        //
        // var requestBody = new
        // {
        //     prompt,
        //     max_tokens = maxTokens,
        //     stop,
        //     temperature,
        //     top_p = topP,
        //     top_k = topK
        // };
        //
        // return requestBody;
        throw new NotImplementedException("placeholder - fixing");
    }

    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns>A list of text content objects as required by the semantic kernel.</returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using var memoryStream = new MemoryStream();
        response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
        memoryStream.Position = 0;
        using var reader = new StreamReader(memoryStream);
        var responseBody = JsonSerializer.Deserialize<MistralTextResponse>(reader.ReadToEnd());
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
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        // var isInstructModel = modelId.Contains("instruct", StringComparison.OrdinalIgnoreCase);
        // var temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", isInstructModel ? DefaultTemperatureInstruct : DefaultTemperatureNonInstruct);
        // var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        // var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);
        // var converseRequest = new ConverseRequest
        // {
        //     ModelId = modelId,
        //     Messages = messages,
        //     System = systemMessages,
        //     InferenceConfig = new InferenceConfiguration
        //     {
        //         Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", temperature),
        //         TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "top_p", isInstructModel ? DefaultTopPInstruct : DefaultTopPNonInstruct),
        //         MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", isInstructModel ? DefaultMaxTokensInstruct : DefaultMaxTokensNonInstruct)
        //     },
        //     AdditionalModelRequestFields = new Document(),
        //     AdditionalModelResponseFieldPaths = new List<string>()
        // };
        // return converseRequest;
        throw new NotImplementedException("placeholder - fixing");
    }

    /// <summary>
    /// Extracts the text generation streaming output from the Mistral response object structure.
    /// </summary>
    /// <param name="chunk"></param>
    /// <returns></returns>
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
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
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        // var isInstructModel = modelId.Contains("instruct", StringComparison.OrdinalIgnoreCase);
        // var temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", isInstructModel ? DefaultTemperatureInstruct : DefaultTemperatureNonInstruct);
        // var messages = BedrockModelUtilities.BuildMessageList(chatHistory);
        // var systemMessages = BedrockModelUtilities.GetSystemMessages(chatHistory);
        // var converseRequest = new ConverseStreamRequest()
        // {
        //     ModelId = modelId,
        //     Messages = messages,
        //     System = systemMessages,
        //     InferenceConfig = new InferenceConfiguration
        //     {
        //         Temperature = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "temperature", temperature),
        //         TopP = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "top_p", isInstructModel ? DefaultTopPInstruct : DefaultTopPNonInstruct),
        //         MaxTokens = BedrockModelUtilities.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", isInstructModel ? DefaultMaxTokensInstruct : DefaultMaxTokensNonInstruct)
        //     },
        //     AdditionalModelRequestFields = new Document(),
        //     AdditionalModelResponseFieldPaths = new List<string>()
        // };
        // return converseRequest;
        throw new NotImplementedException("placeholder - fixing");
    }
}
