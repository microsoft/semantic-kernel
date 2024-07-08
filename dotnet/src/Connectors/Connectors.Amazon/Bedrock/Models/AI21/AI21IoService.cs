// Copyright (c) Microsoft. All rights reserved.

using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.AI21;

public class AI21IoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
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
        var ai21Request = new AI21Request.AI21ChatCompletionRequest
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
            MaxTokens = this.GetExtensionDataValue<int>(settings?.ExtensionData, "max_tokens", 4096)
        },
        StopSequences = this.GetExtensionDataValue<List<string>>(settings?.ExtensionData, "stop_sequences", null),
        NumResponses = this.GetExtensionDataValue<int>(settings?.ExtensionData, "n", 1),
        FrequencyPenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "frequency_penalty", 0.0),
        PresencePenalty = this.GetExtensionDataValue<double>(settings?.ExtensionData, "presence_penalty", 0.0)
    };

    var converseRequest = new ConverseRequest
    {
        ModelId = modelId,
        Messages = ai21Request.Messages,
        System = ai21Request.System,
        InferenceConfig = ai21Request.InferenceConfig,
        AdditionalModelRequestFields = new Document
        {
            // { "stop_sequences", new Document(ai21Request.StopSequences?.Select(s => new Document(s)).ToList() ?? new List<Document>()) },
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
}
