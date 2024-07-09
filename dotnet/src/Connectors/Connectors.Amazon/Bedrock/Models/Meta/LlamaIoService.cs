// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Meta;

public class LlamaIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
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
        var llamaRequest = new LlamaRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = MapRole(m.Role),
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            Temperature = this.GetExtensionDataValue<double>(settings?.ExtensionData, "temperature", 0.5),
            TopP = this.GetExtensionDataValue<double>(settings?.ExtensionData, "top_p", 0.9),
            MaxGenLen = this.GetExtensionDataValue<int>(settings?.ExtensionData, "max_gen_len", 512)
        };
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = llamaRequest.Messages,
            System = llamaRequest.System,
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = (float)llamaRequest.Temperature,
                TopP = (float)llamaRequest.TopP,
                MaxTokens = llamaRequest.MaxGenLen
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>(),
            GuardrailConfig = null,
            ToolConfig = null
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

    private string GetLlamaPrompt(List<Message> messages, List<SystemContentBlock> system)
    {
        var prompt = new StringBuilder();

        if (system?.Any() == true)
        {
            prompt.Append("<s>[INST] <<SYS>>");
            prompt.Append(system.First().Text);
            prompt.Append("<</SYS>>");
            prompt.AppendLine();
        }

        foreach (var message in messages)
        {
            if (message.Role == ConversationRole.User)
            {
                prompt.Append(message.Content.First().Text);
                prompt.Append(" [/INST]");
            }
        }

        return prompt.ToString();
    }
}
