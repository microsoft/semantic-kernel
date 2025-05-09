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
    protected const int ResultTimeoutInSeconds = 15;

    protected ChatCompletionAgent CreateAgent(string instructions, string? name = null, string? description = null)
    {
        return
            new ChatCompletionAgent
            {
                Instructions = instructions,
                Name = name,
                Description = description,
                Kernel = this.CreateKernelWithChatCompletion(),
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
