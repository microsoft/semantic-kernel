// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Mistral;

/// <summary>
/// Input-output service for Mistral.
/// </summary>
public class MistralIOService : IBedrockModelIOService
{
    private readonly BedrockUtilities _util = new();
    // Define constants for default values
    private const float DefaultTemperatureInstruct = 0.5f;
    private const float DefaultTopPInstruct = 0.9f;
    private const int DefaultMaxTokensInstruct = 512;
    private const int DefaultTopKInstruct = 50;
    private static readonly List<string> DefaultStopSequencesInstruct = new List<string>();

    private const float DefaultTemperatureNonInstruct = 0.7f;
    private const float DefaultTopPNonInstruct = 1.0f;
    private const int DefaultMaxTokensNonInstruct = 8192;
    private const int DefaultTopKNonInstruct = 0;
    private static readonly List<string> DefaultStopSequencesNonInstruct = new List<string>();
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by Mistral.
    /// </summary>
    /// <param name="modelId">The model ID to be used as a request parameter.</param>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string modelId, string prompt, PromptExecutionSettings? executionSettings = null)
    {
        var isInstructModel = modelId.Contains("instruct", StringComparison.OrdinalIgnoreCase);
        var temperature = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "temperature", isInstructModel ? (double?)DefaultTemperatureInstruct : (double?)DefaultTemperatureNonInstruct);
        var topP = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_p", isInstructModel ? (double?)DefaultTopPInstruct : (double?)DefaultTopPNonInstruct);
        var maxTokens = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "max_tokens", isInstructModel ? (int?)DefaultMaxTokensInstruct : (int?)DefaultMaxTokensNonInstruct);
        var stop = this._util.GetExtensionDataValue<List<string>>(executionSettings?.ExtensionData, "stop", isInstructModel ? DefaultStopSequencesInstruct : DefaultStopSequencesNonInstruct);
        var topK = this._util.GetExtensionDataValue(executionSettings?.ExtensionData, "top_k", isInstructModel ? (int?)DefaultTopKInstruct : (int?)DefaultTopKNonInstruct);

        var requestBody = new
        {
            prompt,
            max_tokens = maxTokens,
            stop,
            temperature,
            top_p = topP,
            top_k = topK
        };

        return requestBody;
    }
    /// <summary>
    /// Extracts the test contents from the InvokeModelResponse as returned by the Bedrock API.
    /// </summary>
    /// <param name="response">The InvokeModelResponse object provided by the Bedrock InvokeModelAsync output.</param>
    /// <returns>A list of text content objects as required by the semantic kernel.</returns>
    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<MistralRequest.MistralTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Outputs != null && responseBody.Outputs.Count > 0)
                {
                    foreach (var output in responseBody.Outputs)
                    {
                        textContents.Add(new TextContent(output.Text));
                    }
                }
                return textContents;
            }
        }
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
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(settings);
        var request = this.CreateChatCompletionRequest(modelId, false, chatHistory, mistralExecutionSettings, new Kernel());
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = request.Messages.Select(m => new Message
            {
                Role = m.Role,
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = (float)request.Temperature,
                TopP = (float)request.TopP,
                MaxTokens = request.MaxTokens
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>()
        };
        return converseRequest;
    }

    private MistralRequest.MistralChatCompletionRequest CreateChatCompletionRequest(
        string modelId,
        bool stream,
        ChatHistory chatHistory,
        MistralAIPromptExecutionSettings? executionSettings = null,
        Kernel? kernel = null)
    {
        var isInstructModel = modelId.Contains("instruct", StringComparison.OrdinalIgnoreCase);
        float defaultTemperature = isInstructModel ? DefaultTemperatureInstruct : DefaultTemperatureNonInstruct;
        float defaultTopP = isInstructModel ? DefaultTopPInstruct : DefaultTopPNonInstruct;
        int defaultMaxTokens = isInstructModel ? DefaultMaxTokensInstruct : DefaultMaxTokensNonInstruct;
        int defaultTopK = isInstructModel ? DefaultTopKInstruct : DefaultTopKNonInstruct;

        var request = new MistralRequest.MistralChatCompletionRequest(modelId)
        {
            Stream = stream,
            Messages = chatHistory.SelectMany(chatMessage => this.ToMistralChatMessages(chatMessage, executionSettings?.ToolCallBehavior)).ToList(),
            Temperature = executionSettings?.Temperature ?? defaultTemperature,
            TopP = executionSettings?.TopP ?? defaultTopP,
            MaxTokens = executionSettings?.MaxTokens ?? defaultMaxTokens,
            TopK = executionSettings?.TopK ?? defaultTopK,
            SafePrompt = executionSettings?.SafePrompt ?? false,
            RandomSeed = executionSettings?.RandomSeed
        };

        executionSettings?.ToolCallBehavior?.ConfigureRequest(kernel, request);

        return request;
    }
    internal List<MistralRequest.MistralChatMessage> ToMistralChatMessages(ChatMessageContent content, MistralAIToolCallBehavior? toolCallBehavior)
    {
        if (content.Role == AuthorRole.Assistant)
        {
            // Handling function calls supplied via ChatMessageContent.Items collection elements of the FunctionCallContent type.
            var message = new MistralRequest.MistralChatMessage(content.Role.ToString(), content.Content ?? string.Empty);
            Dictionary<string, MistralRequest.MistralToolCall> toolCalls = [];
            foreach (var item in content.Items)
            {
                if (item is not FunctionCallContent callRequest)
                {
                    continue;
                }

                if (callRequest.Id is null || toolCalls.ContainsKey(callRequest.Id))
                {
                    continue;
                }

                var arguments = JsonSerializer.Serialize(callRequest.Arguments);
                var toolCall = new MistralRequest.MistralToolCall()
                {
                    Id = callRequest.Id,
                    Function = new MistralFunction(
                        callRequest.FunctionName,
                        callRequest.PluginName)
                    {
                        Arguments = arguments
                    }
                };
                toolCalls.Add(callRequest.Id, toolCall);
            }
            if (toolCalls.Count > 0)
            {
                message.ToolCalls = [.. toolCalls.Values];
            }
            return [message];
        }

        if (content.Role == AuthorRole.Tool)
        {
            List<MistralRequest.MistralChatMessage>? messages = null;
            foreach (var item in content.Items)
            {
                if (item is not FunctionResultContent resultContent)
                {
                    continue;
                }

                messages ??= [];

                var stringResult = ProcessFunctionResult(resultContent.Result ?? string.Empty, toolCallBehavior);
                messages.Add(new MistralRequest.MistralChatMessage(content.Role.ToString(), stringResult));
            }
            if (messages is not null)
            {
                return messages;
            }

            throw new NotSupportedException("No function result provided in the tool message.");
        }

        return [new MistralRequest.MistralChatMessage(content.Role.ToString(), content.Content ?? string.Empty)];
    }

    private static string ProcessFunctionResult(object functionResult, MistralAIToolCallBehavior? toolCallBehavior)
    {
        if (functionResult is string stringResult)
        {
            return stringResult;
        }

        // This is an optimization to use ChatMessageContent content directly
        // without unnecessary serialization of the whole message content class.
        if (functionResult is ChatMessageContent chatMessageContent)
        {
            return chatMessageContent.ToString();
        }

        // For polymorphic serialization of unknown in advance child classes of the KernelContent class,
        // a corresponding JsonTypeInfoResolver should be provided via the JsonSerializerOptions.TypeInfoResolver property.
        // For more details about the polymorphic serialization, see the article at:
        // https://learn.microsoft.com/en-us/dotnet/standard/serialization/system-text-json/polymorphism?pivots=dotnet-8-0
        return JsonSerializer.Serialize(functionResult, toolCallBehavior?.ToolCallResultSerializerOptions);
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
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(settings);
        var request = this.CreateChatCompletionRequest(modelId, false, chatHistory, mistralExecutionSettings, new Kernel());
        var converseStreamRequest = new ConverseStreamRequest()
        {
            ModelId = modelId,
            Messages = request.Messages.Select(m => new Message
            {
                Role = m.Role,
                Content = new List<ContentBlock> { new() { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = (float)request.Temperature,
                TopP = (float)request.TopP,
                MaxTokens = request.MaxTokens
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>()
        };
        return converseStreamRequest;
    }
}
