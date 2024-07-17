// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;
/// <summary>
/// Input-output service for AI21 Labs Jamba model.
/// </summary>
public class AI21JambaIOService : IBedrockModelIOService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIOService<ITextGenerationRequest, ITextGenerationResponse>
{
    /// <summary>
    /// Builds InvokeModel request Body parameter with structure as required by AI21 Labs Jamba model.
    /// </summary>
    /// <param name="prompt">The input prompt for text generation.</param>
    /// <param name="executionSettings">Optional prompt execution settings.</param>
    /// <returns></returns>
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings? executionSettings = null)
    {
        List<AI21JambaRequest.Msg> messages = new List<AI21JambaRequest.Msg>
        {
            new AI21JambaRequest.Msg
            {
                Role = "user",
                Content = prompt
            }
        };

        double? temperature = 1.0; // AI21 Jamba default
        double? topP = 0.9; // AI21 Jamba default
        int? maxTokens = 4096; // AI21 Jamba default
        List<string>? stop = null;
        int? numberOfResponses = 1; // AI21 Jamba default
        double? frequencyPenalty = null;
        double? presencePenalty = null;

        if (executionSettings != null && executionSettings.ExtensionData != null)
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("top_p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens", out var maxTokensValue);
            maxTokens = maxTokensValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop", out var stopValue);
            stop = stopValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("n", out var numberOfResponsesValue);
            numberOfResponses = numberOfResponsesValue as int?;

            executionSettings.ExtensionData.TryGetValue("frequency_penalty", out var frequencyPenaltyValue);
            frequencyPenalty = frequencyPenaltyValue as double?;

            executionSettings.ExtensionData.TryGetValue("presence_penalty", out var presencePenaltyValue);
            presencePenalty = presencePenaltyValue as double?;
        }

        var requestBody = new AI21JambaRequest.AI21TextGenerationRequest
        {
            Messages = messages,
            Temperature = temperature,
            TopP = topP,
            MaxTokens = maxTokens,
            Stop = stop,
            NumberOfResponses = numberOfResponses,
            FrequencyPenalty = frequencyPenalty,
            PresencePenalty = presencePenalty
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
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<AI21JambaResponse.AI21TextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Choices != null && responseBody.Choices.Count > 0)
                {
                    foreach (var choice in responseBody.Choices)
                    {
                        textContents.Add(new TextContent(choice.Message?.Content));
                    }
                }
                return textContents;
            }
        }
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
        var ai21Request = new AI21JambaRequest.AI21ChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = MapRole(m.Role),
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this.GetExtensionDataValue<float>(settings?.ExtensionData, "temperature", 1),
                TopP = this.GetExtensionDataValue<float>(settings?.ExtensionData, "top_p", 1),
                MaxTokens = this.GetExtensionDataValue(settings?.ExtensionData, "max_tokens", 4096),
                StopSequences = this.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", []),
            },
            NumResponses = this.GetExtensionDataValue(settings?.ExtensionData, "n", 1),
            FrequencyPenalty = this.GetExtensionDataValue(settings?.ExtensionData, "frequency_penalty", 0.0),
            PresencePenalty = this.GetExtensionDataValue(settings?.ExtensionData, "presence_penalty", 0.0)
        };

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = ai21Request.Messages,
            System = ai21Request.System,
            InferenceConfig = ai21Request.InferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", ai21Request.NumResponses },
                { "frequency_penalty", ai21Request.FrequencyPenalty },
                { "presence_penalty", ai21Request.PresencePenalty }
            },
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };

        return converseRequest;
    }
    private static ConversationRole MapRole(AuthorRole role)
    {
        string roleStr;
        if (role == AuthorRole.User)
        {
            roleStr = "user";
        }
        else
        {
            roleStr = "assistant";
        }

        return roleStr switch
        {
            "user" => ConversationRole.User,
            "assistant" => ConversationRole.Assistant,
            _ => throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}")
        };
    }

    private TValue GetExtensionDataValue<TValue>(IDictionary<string, object>? extensionData, string key, TValue defaultValue)
    {
        if (extensionData == null || !extensionData.TryGetValue(key, out object? value))
        {
            return defaultValue;
        }

        if (value is TValue typedValue)
        {
            return typedValue;
        }

        return defaultValue;
    }
    /// <summary>
    /// Gets the streamed text output. AI21 Labs Jamba does not support streaming, but otherwise getting the text response body output would look like the following.
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
    /// AI21 Labs Jamba does not support streaming otherwise getting the converse stream output would look like the following (if model ever decides to add).
    /// </summary>
    /// <param name="modelId"></param>
    /// <param name="chatHistory"></param>
    /// <param name="settings"></param>
    /// <returns></returns>
    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        var ai21Request = new AI21JambaRequest.AI21ChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = MapRole(m.Role),
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this.GetExtensionDataValue<float>(settings.ExtensionData, "temperature", 1),
                TopP = this.GetExtensionDataValue<float>(settings.ExtensionData, "top_p", 1),
                MaxTokens = this.GetExtensionDataValue(settings.ExtensionData, "max_tokens", 4096),
                StopSequences = this.GetExtensionDataValue<List<string>>(settings.ExtensionData, "stop_sequences", []),
            },
            NumResponses = this.GetExtensionDataValue(settings.ExtensionData, "n", 1),
            FrequencyPenalty = this.GetExtensionDataValue(settings.ExtensionData, "frequency_penalty", 0.0),
            PresencePenalty = this.GetExtensionDataValue(settings.ExtensionData, "presence_penalty", 0.0)
        };

        var converseStreamRequest = new ConverseStreamRequest
        {
            ModelId = modelId,
            Messages = ai21Request.Messages,
            System = ai21Request.System,
            InferenceConfig = ai21Request.InferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "n", ai21Request.NumResponses },
                { "frequency_penalty", ai21Request.FrequencyPenalty },
                { "presence_penalty", ai21Request.PresencePenalty }
            },
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };
        return converseStreamRequest;
    }
}
