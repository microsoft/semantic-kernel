// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Agents;

/// <summary>
/// Demonstrate service selection for <see cref="ChatCompletionAgent"/> through setting service-id
/// on <see cref="Agent.Arguments"/> and also providing override <see cref="KernelArguments"/>
/// when calling <see cref="ChatCompletionAgent.InvokeAsync(ChatHistory, KernelArguments?, Kernel?, CancellationToken)"/>
/// </summary>
public class ChatCompletion_ServiceSelection(ITestOutputHelper output) : BaseAgentsTest(output)
{
    private const string ServiceKeyGood = "chat-good";
    private const string ServiceKeyBad = "chat-bad";

    [Fact]
    public async Task UseServiceSelectionWithChatCompletionAgentAsync()
    {
        // Create kernel with two instances of IChatCompletionService
        // One service is configured with a valid API key and the other with an
        // invalid key that will result in a 401 Unauthorized error.
        Kernel kernel = CreateKernelWithTwoServices();

        // Define the agent targeting ServiceId = ServiceKeyGood
        ChatCompletionAgent agentGood =
            new()
            {
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { ServiceId = ServiceKeyGood }),
            };

        // Define the agent targeting ServiceId = ServiceKeyBad
        ChatCompletionAgent agentBad =
            new()
            {
                Kernel = kernel,
                Arguments = new KernelArguments(new PromptExecutionSettings() { ServiceId = ServiceKeyBad }),
            };

        // Define the agent with no explicit ServiceId defined
        ChatCompletionAgent agentDefault = new() { Kernel = kernel };

        // Invoke agent as initialized with ServiceId = ServiceKeyGood: Expect agent response
        Console.WriteLine("\n[Agent With Good ServiceId]");
        await InvokeAgentAsync(agentGood);

        // Invoke agent as initialized with ServiceId = ServiceKeyBad: Expect failure due to invalid service key
        Console.WriteLine("\n[Agent With Bad ServiceId]");
        await InvokeAgentAsync(agentBad);

        // Invoke agent as initialized with no explicit ServiceId: Expect agent response
        Console.WriteLine("\n[Agent With No ServiceId]");
        await InvokeAgentAsync(agentDefault);

        // Invoke agent with override arguments where ServiceId = ServiceKeyGood: Expect agent response
        Console.WriteLine("\n[Bad Agent: Good ServiceId Override]");
        await InvokeAgentAsync(agentBad, new(new PromptExecutionSettings() { ServiceId = ServiceKeyGood }));

        // Invoke agent with override arguments where ServiceId = ServiceKeyBad: Expect failure due to invalid service key
        Console.WriteLine("\n[Good Agent: Bad ServiceId Override]");
        await InvokeAgentAsync(agentGood, new(new PromptExecutionSettings() { ServiceId = ServiceKeyBad }));
        Console.WriteLine("\n[Default Agent: Bad ServiceId Override]");
        await InvokeAgentAsync(agentDefault, new(new PromptExecutionSettings() { ServiceId = ServiceKeyBad }));

        // Invoke agent with override arguments with no explicit ServiceId: Expect agent response
        Console.WriteLine("\n[Good Agent: No ServiceId Override]");
        await InvokeAgentAsync(agentGood, new(new PromptExecutionSettings()));
        Console.WriteLine("\n[Bad Agent: No ServiceId Override]");
        await InvokeAgentAsync(agentBad, new(new PromptExecutionSettings()));
        Console.WriteLine("\n[Default Agent: No ServiceId Override]");
        await InvokeAgentAsync(agentDefault, new(new PromptExecutionSettings()));

        // Local function to invoke agent and display the conversation messages.
        async Task InvokeAgentAsync(ChatCompletionAgent agent, KernelArguments? arguments = null)
        {
            try
            {
                await foreach (ChatMessageContent response in agent.InvokeAsync(
                    new ChatMessageContent(AuthorRole.User, "Hello"),
                    options: new() { KernelArguments = arguments }))
                {
                    Console.WriteLine(response.Content);
                }
            }
            catch (HttpOperationException exception)
            {
                Console.WriteLine($"Status: {exception.StatusCode}");
            }
        }
    }

    private Kernel CreateKernelWithTwoServices()
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        if (this.UseOpenAIConfig)
        {
            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                "bad-key",
                serviceId: ServiceKeyBad);

            builder.AddOpenAIChatCompletion(
                TestConfiguration.OpenAI.ChatModelId,
                TestConfiguration.OpenAI.ApiKey,
                serviceId: ServiceKeyGood);
        }
        else
        {
            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                "bad-key",
                serviceId: ServiceKeyBad);

            builder.AddAzureOpenAIChatCompletion(
                TestConfiguration.AzureOpenAI.ChatDeploymentName,
                TestConfiguration.AzureOpenAI.Endpoint,
                TestConfiguration.AzureOpenAI.ApiKey,
                serviceId: ServiceKeyGood);
        }

        return builder.Build();
    }
}
