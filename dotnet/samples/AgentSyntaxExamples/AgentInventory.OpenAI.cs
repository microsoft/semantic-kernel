// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using Microsoft.SemanticKernel;

namespace AgentSyntaxExamples;

public static partial class AgentInventory
{
    public static class OpenAI
    {
        public static ChatCompletionAgent CreateParrotAgent(Kernel kernel) =>
            CreateChatAgent(
                kernel,
                name: ParrotName,
                instructions: ParrotInstructions);

        public static ChatCompletionAgent CreateHostAgent(Kernel kernel) =>
            CreateChatAgent(
                kernel,
                name: HostName,
                instructions: HostInstructions);

        public static ChatCompletionAgent CreateChatAgent(
            Kernel kernel,
            string name,
            string? instructions = null,
            string? description = null)
            =>
                new(
                    kernel,
                    instructions,
                    description,
                    name)
                {
                    ExecutionSettings = new OpenAIPromptExecutionSettings() { ToolCallBehavior = ToolCallBehavior.AutoInvokeKernelFunctions },
                };
    }
}
