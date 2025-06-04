// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Base class for samples that demonstrate the usage of host agents
/// based on API's such as Open AI Assistants or Azure AI Agents.
/// </summary>
public abstract class BaseOrchestrationTest(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected const int ResultTimeoutInSeconds = 30;

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

    protected sealed class OrchestrationMonitor
    {
        public ChatHistory History { get; } = [];

        public ValueTask ResponseCallback(ChatMessageContent response)
        {
            this.History.Add(response);
            return ValueTask.CompletedTask;
        }
    }
}
