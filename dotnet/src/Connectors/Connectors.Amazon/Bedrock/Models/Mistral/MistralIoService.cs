// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;
using Connectors.Amazon.Core.Responses;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Connectors.Amazon.Models.Mistral;

public class MistralIoService : IBedrockModelIoService<IChatCompletionRequest, IChatCompletionResponse>,
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
        var mistralExecutionSettings = MistralAIPromptExecutionSettings.FromExecutionSettings(settings);
        var request = this.CreateChatCompletionRequest(modelId, false, chatHistory, mistralExecutionSettings, new Kernel());
        var converseRequest = new ConverseRequest
        {
            ModelId = modelId,
            Messages = request.Messages.Select(m => new Message
            {
                Role = m.Role,
                Content = new List<ContentBlock> { new ContentBlock { Text = m.Content } }
            }).ToList(),
            System = new List<SystemContentBlock>(),
            InferenceConfig = new InferenceConfiguration
            {
                Temperature = (float)request.Temperature,
                TopP = (float)request.TopP,
                MaxTokens = (int)request.MaxTokens
            },
            // InferenceConfig = new InferenceConfiguration
            // {
            //     Temperature = 0.7f, // Default value
            //     TopP = 0.9f, // Default value
            //     MaxTokens = 512 // Default value
            // },
            AdditionalModelRequestFields = new Document(),
            AdditionalModelResponseFieldPaths = new List<string>()
        };
        return converseRequest;
    }

    private MistralRequest.MistralChatCompletionRequest CreateChatCompletionRequest(string modelId, bool stream, ChatHistory chatHistory, MistralAIPromptExecutionSettings executionSettings, Kernel? kernel = null)
    {
        var request = new MistralRequest.MistralChatCompletionRequest(modelId)
        {
            Stream = stream,
            Messages = chatHistory.SelectMany(chatMessage => this.ToMistralChatMessages(chatMessage, executionSettings?.ToolCallBehavior)).ToList(),
            Temperature = executionSettings?.Temperature ?? 0.7,
            TopP = executionSettings?.TopP ?? 1,
            MaxTokens = executionSettings?.MaxTokens ?? 8192,
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

    private static string? ProcessFunctionResult(object functionResult, MistralAIToolCallBehavior? toolCallBehavior)
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
}
