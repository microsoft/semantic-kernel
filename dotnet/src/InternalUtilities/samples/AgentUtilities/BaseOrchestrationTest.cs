// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base class for samples that demonstrate the usage of host agents
/// based on API's such as Open AI Assistants or Azure AI Agents.
/// </summary>
public abstract class BaseOrchestrationTest(ITestOutputHelper output) : BaseAgentsTest(output)
{
    protected const int ResultTimeoutInSeconds = 10;

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
}
