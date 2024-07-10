// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Anthropic;

public class AnthropicIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        double? temperature = 1.0; // Claude default
        double? topP = 1.0; // Claude default
        int? maxTokensToSample = 200; // Claude default
        List<string>? stopSequences = new List<string> { "\n\nHuman:" }; // Claude default

        if (executionSettings != null && executionSettings.ExtensionData != null)
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("top_p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens_to_sample", out var maxTokensToSampleValue);
            maxTokensToSample = maxTokensToSampleValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop_sequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;

            executionSettings.ExtensionData.TryGetValue("top_k", out var topKV);
            int? topK = topKV as int?;
        }

        var requestBody = new ClaudeRequest.ClaudeTextGenerationRequest()
        {
            Prompt = $"\n\nHuman: {prompt}\n\nAssistant:",
            MaxTokensToSample = maxTokensToSample,
            StopSequences = stopSequences,
            Temperature = temperature,
            TopP = topP,
            TopK = executionSettings?.ExtensionData?.TryGetValue("top_k", out var topKValue) == true ? topKValue as int? : null
        };

        return requestBody;
    }

    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        using (var memoryStream = new MemoryStream())
        {
            response.Body.CopyToAsync(memoryStream).ConfigureAwait(false).GetAwaiter().GetResult();
            memoryStream.Position = 0;
            using (var reader = new StreamReader(memoryStream))
            {
                var responseBody = JsonSerializer.Deserialize<ClaudeResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (!string.IsNullOrEmpty(responseBody?.Completion))
                {
                    textContents.Add(new TextContent(responseBody.Completion));
                }

                return textContents;
            }
        }
    }

    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings? settings = null)
    {
        var claudeRequest = new ClaudeRequest.ClaudeChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = MapRole(m.Role),
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(), // { new SystemContentBlock { Text = "You are an AI assistant." } },
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = this.GetExtensionDataValue<float>(settings?.ExtensionData, "temperature", 1f),
                TopP = this.GetExtensionDataValue<float>(settings?.ExtensionData, "top_p", 0.999f),
                MaxTokens = this.GetExtensionDataValue<int>(settings?.ExtensionData, "max_tokens", 512) //different for diff models need to change
            },
            // AnthropicVersion = "bedrock-2023-05-31",
            Tools = this.GetExtensionDataValue<List<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeTool>>(settings?.ExtensionData, "tools", null),
            ToolChoice = this.GetExtensionDataValue<ClaudeRequest.ClaudeChatCompletionRequest.ClaudeToolChoice>(settings?.ExtensionData, "tool_choice", null)
        };

        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = claudeRequest.Messages,
            System = claudeRequest.System,
            InferenceConfig = claudeRequest.InferenceConfig,
            AdditionalModelRequestFields = new Document
            {
                { "anthropic_version", claudeRequest.AnthropicVersion },
                {
                    "tools", new Document(claudeRequest.Tools?.Select(t => new Document
                    {
                        { "name", t.Name },
                        { "description", t.Description },
                        { "input_schema", t.InputSchema }
                    }).ToList() ?? new List<Document>())
                },
                {
                    "tool_choice", claudeRequest.ToolChoice != null
                        ? new Document
                        {
                            { "type", claudeRequest.ToolChoice.Type },
                            { "name", claudeRequest.ToolChoice.Name }
                        }
                        : new Document()
                }
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

    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk?["completion"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }

    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        throw new NotImplementedException();
    }
}
