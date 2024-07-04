// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.Extensions.Azure;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Amazon;

public class AmazonIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
    IBedrockModelIoService<ITextGenerationRequest, ITextGenerationResponse>
{
    public ITextGenerationRequest GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        var textGenerationConfig = new TitanRequest.TitanTextGenerationRequest
        {
            InputText = prompt,
            TextGenerationConfig = new TitanRequest.AmazonTitanTextGenerationConfig
            {
                Temperature = (double)executionSettings.ExtensionData?["temperature"],
                TopP = (double)executionSettings.ExtensionData?["topP"],
                MaxTokenCount = (int)executionSettings.ExtensionData?["maxTokenCount"],
                StopSequences = (IList<string>)executionSettings.ExtensionData?["stopSequences"]
            }
        };
        if (executionSettings.ExtensionData == null)
        {
            executionSettings.ExtensionData = new Dictionary<string, object>();
        }
        executionSettings.ExtensionData["textGenerationConfig"] = textGenerationConfig.TextGenerationConfig;

        return textGenerationConfig;
    }

    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory)
    {
        var titanRequest = new TitanRequest.TitanChatGenerationRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = ConversationRole.User,
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(), // { new SystemContentBlock { Text = "You are an AI assistant." } },
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = 0.7f, // Default value
                TopP = 0.9f, // Default value
                MaxTokens = 512 // Default value
            },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>()
        };
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = titanRequest.Messages,
            System = titanRequest.System,
            InferenceConfig = titanRequest.InferenceConfig,
            AdditionalModelRequestFields = titanRequest.AdditionalModelRequestFields,
            AdditionalModelResponseFieldPaths = titanRequest.AdditionalModelResponseFieldPaths,
            GuardrailConfig = null, // Set if needed
            ToolConfig = null // Set if needed
        };
        return converseRequest;
    }

    private static ConversationRole MapRole(string role)
    {
        return role.ToLowerInvariant() switch
        {
            "user" => ConversationRole.User,
            "assistant" => ConversationRole.Assistant,
            _ => throw new ArgumentOutOfRangeException(nameof(role), $"Invalid role: {role}")
        };
    }
}
