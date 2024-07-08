// Copyright (c) Microsoft. All rights reserved.

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
        throw new NotImplementedException();
    }

    public IReadOnlyList<TextContent> GetInvokeResponseBody(InvokeModelResponse response)
    {
        throw new NotImplementedException();
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
}
