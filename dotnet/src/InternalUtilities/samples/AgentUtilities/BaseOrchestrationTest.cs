// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Base class for samples that demonstrate the usage of host agents
/// based on API's such as Open AI Assistants or Azure AI Agents.
/// </summary>
public abstract class BaseOrchestrationTest(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected const int ResultTimeoutInSeconds = 60;

    protected virtual bool EnableLogging => true;

    protected new ILoggerFactory LoggerFactory => this.EnableLogging ? base.LoggerFactory : NullLoggerFactory.Instance;

    protected ChatCompletionAgent CreateAgent(string instructions, string? description = null, string? name = null, Kernel? kernel = null)
    {
        return
            new ChatCompletionAgent
            {
                Name = name,
                Description = description,
                Instructions = instructions,
                Kernel = kernel ?? this.CreateKernelWithChatCompletion(),
            };
    }

    protected static void WriteResponse(ChatMessageContent response)
    {
        if (!string.IsNullOrEmpty(response.Content))
        {
            System.Console.WriteLine($"\n# RESPONSE {response.Role}{(response.AuthorName is not null ? $" - {response.AuthorName}" : string.Empty)}: {response}");
        }
    }

    protected static void WriteStreamedResponse(IEnumerable<StreamingChatMessageContent> streamedResponses)
    {
        string? authorName = null;
        AuthorRole? authorRole = null;
        StringBuilder builder = new();
        foreach (StreamingChatMessageContent response in streamedResponses)
        {
            authorName ??= response.AuthorName;
            authorRole ??= response.Role;

            if (!string.IsNullOrEmpty(response.Content))
            {
                builder.Append($"({JsonSerializer.Serialize(response.Content)})");
            }
        }

        if (builder.Length > 0)
        {
            System.Console.WriteLine($"\n# STREAMED {authorRole ?? AuthorRole.Assistant}{(authorName is not null ? $" - {authorName}" : string.Empty)}: {builder}\n");
        }
    }

    protected sealed class OrchestrationMonitor
    {
        public List<StreamingChatMessageContent> StreamedResponses = [];

        public ChatHistory History { get; } = [];

        public ValueTask ResponseCallback(ChatMessageContent response)
        {
            this.History.Add(response);
            WriteResponse(response);
            return ValueTask.CompletedTask;
        }

        public ValueTask StreamingResultCallback(StreamingChatMessageContent streamedResponse, bool isFinal)
        {
            this.StreamedResponses.Add(streamedResponse);

            if (isFinal)
            {
                WriteStreamedResponse(this.StreamedResponses);
                this.StreamedResponses.Clear();
            }

            return ValueTask.CompletedTask;
        }
    }
}
