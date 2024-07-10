// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using Amazon.BedrockRuntime;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Amazon.Runtime.EventStreams;
using Amazon.Runtime.EventStreams.Internal;
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
                Role = MapRole(m.Role),
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
    // public IEnumerable<StreamingTextContent> GetStreamingInvokeResponseBody(InvokeModelWithResponseStreamResponse response, string modelId)
    // {
    //     var streamingTextContents = new List<StreamingTextContent>();
    //
    //     using (var responseStream = response.Body)
    //     {
    //         responseStream.InitialResponseReceived += OnInitialResponseReceived;
    //         responseStream.ChunkReceived += OnChunkReceived;
    //
    //         responseStream.StartProcessing();
    //         Console.WriteLine("HERE0: " + response.ContentLength);
    //
    //         void OnInitialResponseReceived(object sender, EventStreamEventReceivedArgs<InitialResponseEvent> args)
    //         {
    //             // Handle the initial response event if needed
    //         }
    //
    //         void OnChunkReceived(object sender, EventStreamEventReceivedArgs<PayloadPart> args)
    //         {
    //             var payloadPart = args.EventStreamEvent;
    //             var decodedPayload = Encoding.UTF8.GetString(payloadPart.Bytes.GetBuffer());
    //             var titanStreamResponse = JsonSerializer.Deserialize<TitanTextResponse.TitanStreamResponse>(decodedPayload);
    //
    //             if (titanStreamResponse != null && titanStreamResponse.Chunks != null)
    //             {
    //                 var decodedResponse = titanStreamResponse.GetDecodedResponse();
    //                 streamingTextContents.Add(new StreamingTextContent(
    //                     text: decodedResponse.OutputText,
    //                     choiceIndex: 0, // Assuming a single choice
    //                     modelId: modelId,
    //                     innerContent: decodedResponse,
    //                     metadata: new Dictionary<string, object?>
    //                     {
    //                         { "InputTextTokenCount", decodedResponse.InputTextTokenCount },
    //                         { "TotalOutputTextTokenCount", decodedResponse.TotalOutputTextTokenCount },
    //                         { "CompletionReason", decodedResponse.CompletionReason }
    //                     }));
    //             }
    //             Console.WriteLine("HERE: " + streamingTextContents[0]);
    //         }
    //     }
    //
    //     return streamingTextContents;
    // }
    public IEnumerable<string> GetTextStreamOutput(JsonNode chunk)
    {
        var text = chunk?["outputText"]?.ToString();
        if (!string.IsNullOrEmpty(text))
        {
            yield return text;
        }
    }

    public ConverseStreamRequest GetConverseStreamRequest(string modelId, ChatHistory chatHistory, PromptExecutionSettings settings)
    {
        var titanRequest = new TitanRequest.TitanChatCompletionRequest
        {
            Messages = chatHistory.Select(m => new Message
            {
                Role = MapRole(m.Role),
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

        var converseStreamRequest = new ConverseStreamRequest
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

        return converseStreamRequest;
    }
}
