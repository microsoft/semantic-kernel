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
    public object GetInvokeModelRequestBody(string prompt, PromptExecutionSettings executionSettings)
    {
        double? temperature = 0.7;
        double? topP = 0.9;
        int? maxTokenCount = 512;
        List<string>? stopSequences = [];

        if (executionSettings != null && executionSettings.ExtensionData != null)
        {
            executionSettings.ExtensionData.TryGetValue("temperature", out var temperatureValue);
            temperature = temperatureValue as double?;

            executionSettings.ExtensionData.TryGetValue("top_p", out var topPValue);
            topP = topPValue as double?;

            executionSettings.ExtensionData.TryGetValue("max_tokens", out var maxTokensValue);
            maxTokenCount = maxTokensValue as int?;

            executionSettings.ExtensionData.TryGetValue("stop_sequences", out var stopSequencesValue);
            stopSequences = stopSequencesValue as List<string>;
        }
        var requestBody = new
        {
            inputText = prompt,
            textGenerationConfig = new
            {
                temperature,
                topP,
                maxTokenCount,
                stopSequences
            }
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
                var responseBody = JsonSerializer.Deserialize<TitanTextResponse>(reader.ReadToEnd());
                var textContents = new List<TextContent>();

                if (responseBody?.Results != null && responseBody.Results.Count > 0)
                {
                    string outputText = responseBody.Results[0].OutputText;
                    textContents.Add(new TextContent(outputText));
                }

                return textContents;
            }
        }
    }

    //NOT ACCOUNTING FOR SETTINGS - HARD CODED
    public ConverseRequest GetConverseRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        var titanRequest = new TitanRequest.TitanChatCompletionRequest
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
